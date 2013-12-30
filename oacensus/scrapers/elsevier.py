from bs4 import BeautifulSoup
from oacensus.models import JournalList
from oacensus.models import Publisher
from oacensus.scraper import JournalScraper
import cPickle as pickle
import os
import re
import requests
import string

class ElsevierJournals(JournalScraper):
    """
    Scrape journal names from Elsevier website.
    """
    aliases = ['elsevier']

    _settings = {
            "base-url" : ("Base url to scrape.", "http://www.elsevier.com/journals/title/"),
            "data-file" : ("file to save data under", "elsevier-journal-list.html"),
            "non-alpha-pages" : (
                "List of all pages to scrape which are named something other than a letter of the alphabet.",
                ['other']
                ),
            }

    def scrape(self):
        journals = []
        pages = [l for l in string.ascii_lowercase] + self.setting('non-alpha-pages')

        for page in pages:
            self.print_progress("  fetching page %s" % page)
            url = "%s%s" % (self.setting('base-url'), page)

            response = requests.get(url)
            soup = BeautifulSoup(response.text)

            journal_list = soup.find('ul', class_="listing")
            for entry in journal_list.findAll('li'):
                anchor = entry.find('a')
                journal_info = {}
                issn_ok = False

                journal_url = anchor.get('href')

                if journal_url.startswith('/'):
                    journal_url = "https://www.elsevier.com" + journal_url

                journal_info['url'] = journal_url
                journal_info['title'] = anchor.text.strip()

                if "combined-subscription" in journal_url:
                    continue

                issn_match = re.search("/([0-9a-z]{4}-[0-9a-z]{4})$", journal_url)
                if issn_match:
                    self.print_progress("  don't need to fetch %s" % journal_url)
                    issn_ok = True
                    issn = issn_match.groups()[0]
                    journal_info['issn'] = issn
                    journals.append(journal_info)

                else:
                    # ISSN is not in url, need to parse journal page.
                    #
                    # Pages don't always load correctly, so use multiple
                    # attempts so one load failure doesn't mean we have to
                    # start all over.
                    attempts = 5
                    for i in range(1, attempts):
                        self.print_progress("  fetching %s attempt %s" % (journal_url, i))

                        try:
                            response = requests.get(journal_url)
                        except Exception as e:
                            print e
                            continue

                        self.print_progress("  fetched. parsing...")
                        journal_soup = BeautifulSoup(response.text)
                        if_table = journal_soup.select(".ifContainer .ifTD")
                        if if_table:
                            issn_div = if_table[-1]
                            if "ISSN" in issn_div.text:
                                issn_ok = True
                                issn = issn_div.text.replace("ISSN:", "").strip()
                                journal_info['issn'] = issn
                                journals.append(journal_info)
                                break

                        else:
                            if journal_soup.find('title').text == "Subjects | Elsevier":
                                issn_ok = True
                                break

                    if not issn_ok:
                        raise Exception("Issn not found in %s after %s tries." % (journal_url, attempts))

        filepath = os.path.join(self.work_dir(), self.setting('data-file'))
        with open(filepath, 'wb') as f:
            pickle.dump(journals, f)

    def process(self):
        filepath = os.path.join(self.cache_dir(), self.setting('data-file'))
        with open(filepath, 'rb') as f:
            journals = pickle.load(f)

        elsevier_list = JournalList.create(name="Elsevier Journals")
        publisher = Publisher.create(name="Elsevier")
        for journal_info in journals:
            issn = journal_info['issn']
            params = {
                    'title' : journal_info['title'],
                    'issn' : journal_info['issn'],
                    'url' : journal_info['url'],
                    'publisher' : publisher
                    }

            self.create_or_modify_journal(issn, params, elsevier_list)

        return elsevier_list
