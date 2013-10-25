from bs4 import BeautifulSoup
from oacensus.scraper import Scraper
import codecs
import json
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
            'standard-params' : (
                "Params used in every request.",
                {'func' : 'browse', 'uiLanguage' : 'en' }
                )
            }

    def number_of_pages(self):
        """
        Scrape the initial page to determine how many total pages there are.
        """
        self.print_progress("determining number of pages...")
        result = requests.get(
                self.setting('base-url'),
                params = self.setting('standard-params')
            )

        soup = BeautifulSoup(result.text)

        key = "div.resultLabel table tr td"
        listing = soup.select(key)[1]

        m = re.search("of ([0-9]+)", listing.text)
        assert m is not None
        return int(m.groups()[0])

    def scrape(self):
        journals = []

        n = self.number_of_pages()

        for page_index in range(n):
            self.print_progress("processing page %s of %s" % (page_index+1, n))

            params = { 'page' : page_index+1 }
            params.update(self.setting('standard-params'))

            result = requests.get(
                    self.setting('base-url'),
                    params = params)

            page_filepath = os.path.join(self.work_dir(), "data-%s.html" % page_index)

            with codecs.open(page_filepath, 'wb', encoding="utf-8") as f:
                # Store contents in cache.
                f.write(result.text)

            self.print_progress("  processing %s" % page_filepath)

            soup = BeautifulSoup(result.text)

            entries_per_page = 100

            for i in range(1, entries_per_page):
                if i % 10 == 0:
                    self.print_progress("  processing journal %s" % i)

                journal_info = {}

                select = "#record%s" % i
                records = soup.select(select)

                if not records:
                    break

                record = records[0]

                data = record.find("div", class_="data")
                link = data.find("a")

                journal_info['title'] = link.find("b").text.strip()
                journal_info['url'] = link['href'].replace(u"/doaj?func=further&amp;passme=", u"")

                issn_label = data.find("strong")
                assert issn_label.text == "ISSN/EISSN"
                issn_data = issn_label.next_sibling.strip().split(" ")
                assert issn_data[0] == u':'
                journal_info['issn'] = "%s-%s" % (issn_data[1][0:4], issn_data[1][4:8])
                if len(issn_data) == 3:
                    journal_info['eissn'] = "%s-%s" % (issn_data[2][0:4], issn_data[2][4:8])

                if len(data.find_all("strong")) > 1:
                    subject_label = data.find_all("strong")[1]
                    assert subject_label.text == "Subject"
                    subject_link = subject_label.next_sibling.next_sibling
                    assert "func=subject" in subject_link['href']
                    journal_info['subject'] = subject_link.text.strip()

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

                journals.append(journal_info)

        journals_filepath = os.path.join(self.work_dir(), "journals-data.json")
        with open(journals_filepath, 'wb') as f:
            json.dump(journals, f)

    def process(self):
        from oacensus.models import Journal

        journals_filepath = os.path.join(self.cache_dir(), "journals-data.json")
        with open(journals_filepath, 'rb') as f:
            journals = json.load(f)

        for journal_info in journals:
            journal = Journal.by_issn(journal_info['issn'])
            if journal:
                journal.open_access = True # because on doaj website
                journal.open_access_source = self.alias
                journal.license = journal_info['license']
                journal.save()
