from bs4 import BeautifulSoup
from oacensus.scraper import Scraper
import glob
import hashlib
import json
import os
import re
import string
import urllib

class ElsevierJournals(Scraper):
    """
    Scrape journal names from Elsevier website.
    """
    aliases = ['elsevier']

    _settings = {
            "base-url" : ("Base url to scrape.", "http://www.elsevier.com/journals/title/"),
            "non-alpha-pages" : (
                "List of all pages named something other than a letter of the alphabet.",
                ['other']
                ),
            "data-file" : ("file to save data under", "elsevier-journal-list.html")
            }

    def scrape(self):
        pages = [l for l in string.ascii_lowercase] + self.setting('non-alpha-pages')
        for page in pages:
            print "  fetching page", page
            url = "%s%s" % (self.setting('base-url'), page)
            filepath = os.path.join(self.work_dir(), "data-%s.html" % page)
            urllib.urlretrieve(url, filepath)

            skip = []

            with open(filepath, 'r') as f:
                soup = BeautifulSoup(f)
                for anchor in self.journal_list_iter(soup):
                    journal_url = anchor.get('href')

                    if "combined-subscription" in journal_url:
                        continue

                    if journal_url.startswith('/'):
                        journal_url = "https://www.elsevier.com" + journal_url

                    issn_found = False

                    m = re.search("/([0-9a-z]{4}-[0-9a-z]{4})$", journal_url)
                    if m:
                        issn = m.groups()[0]
                        issn_found = True
                        print "  found issn", issn, "in url", journal_url
                    else:
                        journal_filename = hashlib.md5(journal_url).hexdigest()
                        journal_filepath = os.path.join(self.work_dir(), journal_filename)

                        n = 5

                        for i in range(1, n):
                            print "  fetching", journal_url, "attempt", i

                            try:
                                urllib.urlretrieve(journal_url, journal_filepath)
                            except IOError:
                                continue

                            with open(journal_filepath, 'rb') as f:
                                journal_soup = BeautifulSoup(f)
                                if_table = journal_soup.select(".ifContainer .ifTD")
                                if if_table:
                                    issn_div = if_table[-1]
                                    if "ISSN" in issn_div.text:
                                        issn_found = True
                                        break
                                else:
                                    if journal_soup.find('title').text == "Subjects | Elsevier":
                                        skip.append(journal_url)
                                        issn_found = True
                                        break

                    if not issn_found:
                        raise Exception("Issn not found in %s after %s tries." % (journal_url, n))

            skip_filepath = os.path.join(self.work_dir(), "skip.json")
            with open(skip_filepath, 'w') as f:
                json.dump(skip, f)


    def journal_list_iter(self, soup):
        journal_list = soup.find('ul', class_="listing")
        for entry in journal_list.findAll('li'):
            anchor = entry.find('a')
            yield anchor

    def process(self):
        from oacensus.models import JournalList
        from oacensus.models import Publisher
        elsevier_list = JournalList.create(name="Elsevier Journals")
        publisher = Publisher.create(name="Elsevier")

        skip_filepath = os.path.join(self.cache_dir(), "skip.json")
        with open(skip_filepath, 'r') as f:
            skip_journals = json.load(f)

        print "journals to skip are", skip_journals

        for filepath in glob.iglob(os.path.join(self.cache_dir(), "data*.html")):
            print "filename", filepath

            with open(filepath, 'rb') as f:
                soup = BeautifulSoup(f)

            for anchor in self.journal_list_iter(soup):
                journal_url = anchor.get('href')

                if journal_url.startswith('/'):
                    journal_url = "https://www.elsevier.com" + journal_url

                if journal_url in skip_journals:
                    print "skipping", journal_url
                    continue

                m = re.search("/([0-9a-z]{4}-[0-9a-z]{4})$", journal_url)
                if m:
                    issn = m.groups()[0]

                else:
                    journal_filename = hashlib.md5(journal_url).hexdigest()
                    journal_filepath = os.path.join(self.cache_dir(), journal_filename)

                    with open(journal_filepath, 'rb') as f:
                        journal_soup = BeautifulSoup(f)
                        if_table = journal_soup.select(".ifContainer .ifTD")
                        issn_div = if_table[-1]
                        if not "ISSN" in issn_div.text:
                            raise Exception("no ISSN found in %s" % issn_div.text)
                        issn = issn_div.text.replace("ISSN:", "").strip()

                from oacensus.models import Journal
                journal = Journal.create(
                        source=self.alias,
                        title = anchor.text.strip(),
                        issn=issn,
                        url = journal_url,
                        publisher = publisher )

                elsevier_list.add_journal(journal)
