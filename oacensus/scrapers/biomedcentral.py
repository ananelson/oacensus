from bs4 import BeautifulSoup
from oacensus.scraper import Scraper
import hashlib
import os
import urllib

class BiomedCentralJournals(Scraper):
    """
    Scrape journal names from BioMed Central, an open access journal publisher.

    This scraper obtains journal names, urls and ISSNs from the BioMed Central
    website.
    """
    aliases = ['biomed']

    _settings = {
            "url" : ("url to scrape", "http://www.biomedcentral.com/journals"),
            "data-file" : ("file to save data under", "bmc-journal-list.html")
            }

    def scrape(self):
        filepath = os.path.join(self.work_dir(), self.setting('data-file'))
        urllib.urlretrieve(self.setting('url'), filepath)

        with open(filepath, 'rb') as f:
            soup = BeautifulSoup(f)

        for anchor in self.journal_list_iter(soup):
            journal_url = anchor.get('href')
            journal_filename = hashlib.md5(journal_url).hexdigest()
            journal_filepath = os.path.join(self.work_dir(), journal_filename)

            issn_found = False
            n = 5
            for i in range(1, n):
                print "  fetching", journal_url, "attempt", i
                urllib.urlretrieve(journal_url, journal_filepath)

                with open(journal_filepath, 'rb') as f:
                    journal_soup = BeautifulSoup(f)
                    issn_span_list = journal_soup.select("#issn")
                    if issn_span_list:
                        issn_found = True
                        break

            if not issn_found:
                raise Exception("Issn not found in %s after %s tries." % (journal_url, n))

    def journal_list_iter(self, soup):
        journal_ul = soup.find("ul", class_="journals")
        for entry in journal_ul.findAll('h3'):
            if 'class' in entry.attrs and 'core-journal-heading' in entry['class']:
                continue # not a real entry

            reached_archived_journals = False
            for parent in entry.parents:
                if parent.attrs.get('id') == "archived-journals":
                    reached_archived_journals = True
                    break
            if reached_archived_journals:
                break

            anchor = entry.find('a')

            yield anchor

    def parse(self):
        from oacensus.models import Journal
        from oacensus.models import JournalList
        from oacensus.models import Publisher

        filepath = os.path.join(self.cache_dir(), self.setting('data-file'))

        with open(filepath, 'rb') as f:
            soup = BeautifulSoup(f)

        biomed_list = JournalList.create(name = "BioMedCentral Journals")
        publisher = Publisher.create(name = "BioMedCentral")

        for anchor in self.journal_list_iter(soup):
            journal_url = anchor.get('href')
            self.print_progress("  parsing %s" % journal_url)
            journal_filename = hashlib.md5(journal_url).hexdigest()
            journal_filepath = os.path.join(self.cache_dir(), journal_filename)

            with open(journal_filepath, 'rb') as f:
                journal_soup = BeautifulSoup(f)

            issn_span_list = journal_soup.select("#issn")
            if issn_span_list:
                issn_span = journal_soup.select("#issn")[0]
                issn = issn_span.text
            else:
                raise Exception("no issn found for %s" % anchor.text.strip())

            journal = Journal.create(
                    source = self.alias,
                    title = anchor.text.strip(),
                    url = anchor.get('href'),
                    issn = issn,
                    publisher = publisher)

            biomed_list.add_journal(journal)
