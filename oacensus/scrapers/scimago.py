from bs4 import BeautifulSoup
from oacensus.scraper import JournalScraper
from oacensus.utils import urlretrieve
import os

class ScimagoJournals(JournalScraper):
    """
    Download Scimago journal info.
    """
    aliases = ['scimago']

    _settings = {
            'base-url' : (
                "BASE url for downloading Scimago data.",
                "http://www.scimagojr.com/journalrank.php"
                ),
            'filename' : 'scimago.html',
            'year' : ("Year for which to return data.", 2012)
            }

    def scrape(self):
        params = {
                'category' : 0,
                'area' : 0,
                'year' : self.setting('year'),
                'country' : '',
                'order' : 'sjr',
                'page' : 0,
                'min' : 0,
                'min_type' : 'cd',
                'out' : 'xls'
                }

        filepath = os.path.join(self.work_dir(), self.setting('filename'))
        url = self.setting('base-url')
        urlretrieve(url, params, filepath)

    def process(self):
        filepath = os.path.join(self.cache_dir(), self.setting('filename'))

        with open(filepath, 'rb') as f:
            soup = BeautifulSoup(f)

        for i, row in enumerate(soup.find_all("tr")):
            if i == 0:
                headers = row.find_all("th")
                assert headers[1].text == "Title"
                assert headers[2].text == "ISSN"
                assert headers[3].text == "SJR"
                assert headers[4].text == "H index"
                assert headers[5].text == "Total Docs. (%s)" % self.setting('year')
                assert headers[6].text == "Total Docs. (3years)"
                assert headers[7].text == "Total Refs."
                assert headers[8].text == "Total Cites (3years)"
                assert headers[9].text == "Citable Docs. (3years)"
                assert headers[10].text == "Cites / Doc. (2years)"
                assert headers[11].text == "Ref. / Doc."
                assert headers[12].text == "Country"
            else:
                cells = row.find_all("td")

                issn = cells[2].text.strip("=\"")

                if issn == '0':
                    continue

                params = {
                        'title' : cells[1].text.strip(),
                        'country' : cells[12].text.strip()
                        }

                self.create_or_modify_journal(issn, params)
