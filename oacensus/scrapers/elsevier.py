from bs4 import BeautifulSoup
from oacensus.models import Journal
from oacensus.models import JournalList
from oacensus.scraper import Scraper
import os
import string
import urllib2

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
            "data-file" : ("file to save data under", "elsevier-journal-list.csv")
            }

    def scrape(self):
        pages = [l for l in string.ascii_lowercase] + self.setting('non-alpha-pages')
        for page in pages:
            url = "%s%s" % (self.setting('base-url'), page)
            filepath = os.path.join(self.work_dir(), "data-%s.html" % page)
            print "loading", url
            with open(filepath, 'wb') as f:
                html = urllib2.urlopen(url).read()
                f.write(html)

    def parse(self):
        elsevier_list = JournalList(name="Elsevier Journals")
        elsevier_list.save()

        for filename in os.listdir(self.cache_dir()):
            filepath = os.path.join(self.cache_dir(), filename)

            with open(filepath, 'rb') as f:
                soup = BeautifulSoup(f)
                journal_list = soup.find('ul', class_="listing")
                for entry in journal_list.findAll('li'):
                    anchor = entry.find('a')
                    journal = Journal(
                            title = anchor.text.strip(),
                            url = anchor.get('href'))
                    journal.save()

                    elsevier_list.add_journal(journal)
