from bs4 import BeautifulSoup
from oacensus.scraper import Scraper
import requests
import os

class ScimagoJournals(Scraper):
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

        result = requests.get(
                self.setting('base-url'),
                params=params,
                stream=True
                )

        filepath = os.path.join(self.work_dir(), self.setting('filename'))
        with open(filepath, "wb") as f:
            for block in result.iter_content(1024):
                if not block:
                    break
                f.write(block)

    def process(self):
        from oacensus.models import Journal

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
                journal = Journal.by_issn(issn)
                if journal:
                    print "found matching journal", journal

                #params = {
                #        'title' : cells[1].text.strip(),
                #        'issn' : cells[2].text.strip("=\""),
                #        'country' : cells[12].text.strip()
                #        }

                #if params['issn'] != '0':
                #    Journal.create_or_update_by_issn(params)


#row is <tr><td>20544</td><td>Zoologische Mededelingen</td><td>="18762174"</td><td>0,000</td><td>0</td><td>1</td><td>0</td><td>18</td><td>0</td><td>0</td><td>0,00</td><td>18,00</td><td>Netherlands</td></tr>
            
