from oacensus.models import JournalList
from oacensus.models import Publisher
from oacensus.scraper import JournalScraper
import csv
import os
import urllib

class DoajJournals(JournalScraper):
    """
    Updates journals in the database with openness information from DOAJ.
    
    Can also optionally add new journals to the database based on DOAJ entries.
    """
    aliases = ['doaj']

    _settings = {
            "csv-url" : ("Base url for accessing DOAJ.", "http://www.doaj.org/csv"),
            'update-journal-fields' : ["open_access", "open_access_source", "license"],
            'data-file' : ("File to save data under.", "doaj.csv")
            }

    def scrape(self):
        url = self.setting('csv-url')
        data_file = os.path.join(self.work_dir(), self.setting('data-file'))
        urllib.urlretrieve(url, data_file)

    def process(self):
        doaj_data = os.path.join(self.cache_dir(), self.setting('data-file'))
        limit = self.setting('limit')
        
        doaj_list = JournalList.create(name = "DOAJ Journals")

        with open(doaj_data, 'rb') as f:
            doaj_reader = csv.DictReader(f)

            for i, row in enumerate(doaj_reader):
                if limit is not None and i >= limit:
                    break

                issn = row['ISSN'] or row['EISSN']

                raw_license = row['CC License']
                if raw_license:
                    license = "CC-%s" % raw_license
                else:
                    license = None

                params = {
                        'title' : row['Title'],
                        'url' : row['Identifier'],
                        'publisher' : Publisher.create_or_update_by_name(row['Publisher']),
                        'eissn' : row['EISSN'],
                        'license' : license,
                        'open_access_source' : self.alias,
                        'open_access' : True
                        }

                j = self.create_or_modify_journal(issn, params, doaj_list)

        return doaj_list
