from oacensus.models import Journal
from oacensus.models import JournalList
from oacensus.models import Publisher
from oacensus.models import License
from oacensus.scraper import RatingScraper
import csv
import os
import urllib

class DoajJournals(RatingScraper):
    """
    Generates ratings for journals with openness information from DOAJ.
    """
    aliases = ['doaj']

    _settings = {
            "cache-expires" : 90,
            "cache-expires-units" : "days",
            "csv-url" : ("Base url for accessing DOAJ.", "http://www.doaj.org/csv"),
            "list-name" : ("Name for JournalList which is created from journals.", "DOAJ Journals"),
            'update-journal-fields' : ["open_access", "open_access_source", "license"],
            'data-file' : ("File to save data under.", "doaj.csv")
            }

    def purge(self):
        Journal.delete().where(Journal.source == self.alias).execute()
        JournalList.delete().where(JournalList.name == self.setting('list-name'))

    def scrape(self):
        data_file = os.path.join(self.work_dir(), self.setting('data-file'))
        url = self.setting('csv-url')
        urllib.urlretrieve(url, data_file)

    def process(self):
        doaj_data = os.path.join(self.cache_dir(), self.setting('data-file'))
        limit = self.setting('limit')
        
        doaj_list = JournalList.create(name = self.setting('list-name'), source=self.alias)

        with open(doaj_data, 'rb') as f:
            doaj_reader = csv.DictReader(f)

            for i, row in enumerate(doaj_reader):
                # Allow limiting to a small number for testing and development.
                if limit is not None and i >= limit:
                    break

                issn = row['ISSN'] or row['EISSN']

                raw_license = row['CC License']
                if raw_license:
                    license = License.find_license_by_alias("cc-%s" % raw_license)

                publisher = Publisher.create_or_update_by_name(row['Publisher'], self.alias)

                params = {
                        'source' : self.alias,
                        'title' : row['Title'],
                        'url' : row['Identifier'],
                        'publisher' : publisher,
                        'eissn' : row['EISSN'],
                        'license' : license,
                        }

                self.create_or_modify_journal(issn, params, doaj_list)

        return doaj_list
