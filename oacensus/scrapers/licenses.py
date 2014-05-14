from oacensus.models import License
from oacensus.models import LicenseAlias
from oacensus.scraper import Scraper
import yaml
from oacensus.utils import project_root
import os

class BuiltinLicenses(Scraper):
    """
    Reads license types from a local definitions file.
    """
    aliases = ['licenses']
    _settings = {
            "cache-expires" : 90,
            "cache-expires-units" : "days",
            "licenses-file" : ("Path to licenses YAML file.", "licenses.yaml")
            }

    def scrape(self):
        pass

    def process(self):
        licenses_file = self.setting('licenses-file')
        licenses_path = os.path.join(project_root, licenses_file)

        with open(licenses_path, 'rb') as f:
            license_data = yaml.safe_load(f)

        for license_alias, license in license_data.iteritems():
            license['alias'] = license_alias

            other_aliases = license['aliases']
            del license['aliases']

            license = License.create(
                    source=self.db_source(),
                     log=self.db_source(),
                    **license)

            for alias in other_aliases:
                LicenseAlias.create(
                        license=license,
                        alias=alias,
                        source=self.db_source(),
                        log=self.db_source()
                        )
