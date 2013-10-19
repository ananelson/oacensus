from oacensus.scraper import Scraper
import os
import urllib2
from bs4 import BeautifulSoup
from oacensus.models import Journal
from oacensus.models import JournalList

class BiomedCentralJournals(Scraper):
    """
    Scrape journal names from biomedcentral.
    """
    aliases = ['biomed']

    _settings = {
            "url" : ("url to scrape", "http://www.biomedcentral.com/journals"),
            "data-file" : ("file to save data under", "bmc-journal-list.csv")
            }

    def scrape(self):
        filepath = os.path.join(self.work_dir(), self.setting('data-file'))
        with open(filepath, 'wb') as f:
            html = urllib2.urlopen(self.setting('url')).read()
            f.write(html)

    def parse(self):
        filepath = os.path.join(self.cache_dir(), self.setting('data-file'))

        with open(filepath, 'rb') as f:
            soup = BeautifulSoup(f)

        biomed_list = JournalList(name = "Biomed Central List")
        biomed_list.save()

        journal_ul = soup.find("ul", class_="journals")

        for entry in journal_ul.findAll('h3'):
            if 'class' in entry.attrs and 'core-journal-heading' in entry['class']:
                continue

            anchor = entry.find('a')
            journal = Journal(
                    title = anchor.text.strip(),
                    url = anchor.get('href'))
            journal.save()
            biomed_list.add_journal(journal)
