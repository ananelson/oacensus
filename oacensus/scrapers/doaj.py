from bs4 import BeautifulSoup
from oacensus.scraper import Scraper
import cPickle as pickle
import os
import re
import requests

class DoajJournals(Scraper):
    """
    Updates journals in the database with openness information from DOAJ.
    """
    aliases = ['doaj']

    _settings = {
            "base-url" : ("Base url for accessing DOAJ.", "http://www.doaj.org/doaj"),
            'data-file' : ("File to save data under.", "doaj.pickle"),
            'standard-params' : (
                "Params used in every request.",
                {'func' : 'browse', 'uiLanguage' : 'en' }
                )
            }

    def request_params(self, params=None):
        if not params:
            params = {}
        params.update(self.setting('standard-params'))
        return params

    def number_of_pages(self):
        """
        Scrape the initial page to determine how many total pages there are.
        """
        self.print_progress("determining number of pages...")

        base_url = self.setting('base-url')
        params = self.request_params()
        result = requests.get(base_url, params=params)

        soup = BeautifulSoup(result.text)
        key = "div.resultLabel table tr td"
        listing = soup.select(key)[1]

        m = re.search("of ([0-9]+)", listing.text)
        assert m is not None
        return int(m.groups()[0])

    def scrape(self):
        journals = {}
        n = self.number_of_pages()

        for page_index in range(n):
            self.print_progress("processing page %s of %s" % (page_index+1, n))

            base_url = self.setting('base-url')
            params = self.request_params({ 'page' : page_index+1 })
            result = requests.get(base_url, params=params)

            soup = BeautifulSoup(result.text)
            results = soup.select("#result")[0]

            for i, record in enumerate(results.children):
                if hasattr(record, 'attrs'):
                    div_id = record.attrs.get('id')
                    if div_id and re.match("^record([0-9]+)$", div_id):
                        self.print_progress("  processing div %s" % div_id)
                    else:
                        continue
                else:
                    continue
                        
                journal_info = {}

                data = record.find("div", class_="data")
                link = data.find("a")

                journal_info['title'] = link.find("b").text.strip()
                journal_info['url'] = link['href'].replace(u"/doaj?func=further&amp;passme=", u"")

                # Parse ISSN and EISSN
                issn_label = data.find("strong")
                assert issn_label.text == "ISSN/EISSN"
                issn_data = issn_label.next_sibling.strip().split(" ")
                assert issn_data[0] == u':'
                journal_info['issn'] = "%s-%s" % (issn_data[1][0:4], issn_data[1][4:8])
                if len(issn_data) == 3:
                    journal_info['eissn'] = "%s-%s" % (issn_data[2][0:4], issn_data[2][4:8])

                # Parse Subject
                if len(data.find_all("strong")) > 1:
                    subject_label = data.find_all("strong")[1]
                    assert subject_label.text == "Subject"
                    subject_link = subject_label.next_sibling.next_sibling
                    assert "func=subject" in subject_link['href']
                    journal_info['subject'] = subject_link.text.strip()

                # Parse Country, Language, Start Year, License
                for item in data.find_all('b'):
                    value = None
                    if item and item.next_sibling:
                        if isinstance(item.next_sibling, basestring):
                            value = item.next_sibling.replace(":", "").strip()

                    if item.text == 'Country':
                        journal_info['country'] = value
                    elif item.text == 'Language':
                        journal_info['language'] = value
                    elif item.text == 'Start year':
                        if value:
                            journal_info['start_year'] = int(value)
                    elif item.text == 'License':
                        journal_info['license'] = item.next_sibling.next_sibling['href']
                    else:
                        pass

                # Save journal info so it can be retrieved by ISSN.
                journals[journal_info['issn']] = journal_info

        journals_filepath = os.path.join(self.work_dir(), self.setting('data-file'))
        with open(journals_filepath, 'wb') as f:
            pickle.dump(journals, f)

    def process(self):
        from oacensus.models import Journal

        journals_filepath = os.path.join(self.cache_dir(), self.setting('data-file'))
        with open(journals_filepath, 'rb') as f:
            doaj_journals = pickle.load(f)

        for journal in Journal.select():
            doaj_info = doaj_journals.get(journal.issn)
            if doaj_info:
                journal.open_access = True # because on doaj website
                journal.open_access_source = self.alias
                journal.license = doaj_info['license']
                journal.save()
