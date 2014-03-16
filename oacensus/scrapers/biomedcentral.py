from bs4 import BeautifulSoup
from oacensus.models import Journal
from oacensus.models import Rating
from oacensus.models import JournalList
from oacensus.models import License
from oacensus.models import Publisher
from oacensus.scraper import JournalScraper
import hashlib
import os
import urllib

class BiomedCentralJournals(JournalScraper):
    """
    Scrape journal names from BioMed Central, an open access journal publisher.

    This scraper obtains journal names, urls and ISSNs from the BioMed Central
    website.
    """
    aliases = ['biomed']

    _settings = {
            "url" : ("url to scrape", "http://www.biomedcentral.com/journals"),
            "data-file" : ("file to save data under", "bmc-journal-list.html"),
            "license" : ("Open access license for BioMedCentral journals.", "cc-by"),
            "issns" : ("Dict of supplemental ISSNs if pages prove difficult to parse.", {
                "http://www.almob.org" : "1748-7188"
                })
            }

    def is_data_stored(self):
        return Journal.count_from_source(self.alias) > 0

    def scrape(self):
        limit = self.setting('limit')
        filepath = os.path.join(self.work_dir(), self.setting('data-file'))
        urllib.urlretrieve(self.setting('url'), filepath)

        with open(filepath, 'rb') as f:
            soup = BeautifulSoup(f)

        for i, anchor in enumerate(self.journal_list_iter(soup)):
            if limit is not None and i >= limit:
                break

            journal_url = anchor.get('href')
            journal_filename = hashlib.md5(journal_url).hexdigest()
            journal_filepath = os.path.join(self.work_dir(), journal_filename)

            issn_found = False
            n_attempts = 5
            for i in range(1, n_attempts):
                self.print_progress("  fetching %s attempt %s" % (journal_url, i))
                urllib.urlretrieve(journal_url, journal_filepath)

                with open(journal_filepath, 'rb') as f:
                    journal_soup = BeautifulSoup(f)
                    issn_span_list = journal_soup.select("#issn")
                    if issn_span_list:
                        issn_found = True
                        break

            if not issn_found and not self.setting('issns').has_key(journal_url):
                raise Exception("Issn not found in %s after %s tries." % (journal_url, n_attempts))

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

    def process(self):
        license = License.find_license(self.setting('license'))
        filepath = os.path.join(self.cache_dir(), self.setting('data-file'))
        with open(filepath, 'rb') as f:
            soup = BeautifulSoup(f)

        biomed_list = JournalList.create(name = "BioMedCentral Journals", source=self.alias)
        publisher = Publisher.create(name = "BioMedCentral", source=self.alias)

        for anchor in self.journal_list_iter(soup):
            journal_url = anchor.get('href')
            self.print_progress("  parsing %s" % journal_url)
            journal_filename = hashlib.md5(journal_url).hexdigest()
            journal_filepath = os.path.join(self.cache_dir(), journal_filename)

            try:
                with open(journal_filepath, 'rb') as f:
                    journal_soup = BeautifulSoup(f)
            except IOError:
                if self.setting('limit') is None:
                    raise
                else:
                    continue

            issn_span_list = journal_soup.select("#issn")
            if issn_span_list:
                issn_span = journal_soup.select("#issn")[0]
                issn = issn_span.text
            else:
                issn = self.setting('issns')[journal_url]

            args = {
                    'title' : anchor.text.strip(),
                    'url' : anchor.get('href'),
                    'publisher' : publisher
                    }

            journal = self.create_or_modify_journal(issn, args, biomed_list)

            Rating.create(
                    journal = journal,
                    free_to_read = True,
                    license = license,
                    source = self.alias
                    )

        return biomed_list
