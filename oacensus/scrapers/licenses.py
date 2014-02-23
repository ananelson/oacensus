from oacensus.models import License
from oacensus.scraper import Scraper
import json
import os
import urllib

class OpenDefinition(Scraper):
    """
    Scrapes open access/open source licensing information from
    opendefinition.org API.
    """
    aliases = ['licenses']
    _settings = {
            "cache-expires" : 90,
            "cache-expires-units" : "days",
            "data-file" : ("File name to save data under.", "all.json"),
            "licenses-url" : ("URL at which all licenses can be downloaded.", "http://licenses.opendefinition.org/licenses/groups/all.json")
            }

    def scrape(self):
        filepath = os.path.join(self.work_dir(), self.setting('data-file'))
        urllib.urlretrieve(self.setting('licenses-url'), filepath)

    def process(self):
        data_file = os.path.join(self.cache_dir(), self.setting('data-file'))
        with open(data_file, 'rb') as f:
            license_data = json.load(f)

        for license in license_data.values():
            license['alias'] = license['id']
            del license['id']
            License.create(source=self.alias, **license)
