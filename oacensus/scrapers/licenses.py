from oacensus.models import License
from oacensus.models import LicenseAlias
from oacensus.scraper import Scraper
import yaml

class BuiltinLicenses(Scraper):
    """
    Reads license types from a local definitions file.
    """
    aliases = ['licenses']
    _settings = {
            "cache-expires" : 90,
            "cache-expires-units" : "days",
            "licenses-file" : ("Path to licenses JSON file.", "oacensus/licenses.yaml")
            }

    def scrape(self):
        pass

    def process(self):
        with open(self.setting('licenses-file'), 'rb') as f:
            license_data = yaml.safe_load(f)

        for license_alias, license in license_data.iteritems():
            license['alias'] = license_alias

            other_aliases = license['aliases']
            del license['aliases']

            license = License.create(
                    source=self.alias,
                    **license)

            for alias in other_aliases:
                LicenseAlias.create(
                        license=license,
                        alias=alias,
                        source=self.alias)
