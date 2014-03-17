from oacensus.models import License
from oacensus.models import Rating
from oacensus.models import Publisher
from oacensus.scraper import JournalScraper
from oacensus.utils import unicode_csv_reader
import codecs
import os
import urllib

class DoajJournals(JournalScraper):
    """
    Generates ratings for journals with openness information from DOAJ.
    """
    aliases = ['doaj']

    _settings = {
            "add-new-journals" : True,
            "cache-expires" : 90,
            "cache-expires-units" : "days",
            "encoding" : "utf-8",
            "csv-url" : ("Base url for accessing DOAJ.", "http://www.doaj.org/csv"),
            'data-file' : ("File to save data under.", "doaj.csv")
            }

    def scrape(self):
        data_file = os.path.join(self.work_dir(), self.setting('data-file'))
        url = self.setting('csv-url')
        urllib.urlretrieve(url, data_file)

    def process(self):
        doaj_data = os.path.join(self.cache_dir(), self.setting('data-file'))
        limit = self.setting('limit')
        
        with codecs.open(doaj_data, 'r', encoding=self.setting('encoding')) as f:
            doaj_reader = unicode_csv_reader(f)

            for i, row in enumerate(doaj_reader):
                if limit is not None and i >= limit:
                    break

                issn = row['ISSN'] or row['EISSN']

                raw_license = row['CC License']
                if raw_license:
                    license = License.find_license("cc-%s" % raw_license)
                else:
                    license = None

                publisher = Publisher.find_or_create_by_name(row['Publisher'], self.alias)

                args = {
                        'title' : row['Title'],
                        'url' : row['Identifier'],
                        'publisher' : publisher
                    }
                journal = self.create_or_modify_journal(issn, args)

                Rating.create(
                        journal = journal,
                        free_to_read = True,
                        license = license,
                        source = self.alias
                        )
