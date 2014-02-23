from oacensus.scraper import Scraper
from oacensus.models import License
from tests.utils import setup_db

setup_db()

def test_license_scraper_all_licenses():
    assert License.select().count() == 0
    scraper = Scraper.create_instance('licenses')
    scraper.run()
    assert License.select().count() > 100

def test_license_scraper_osi_only():
    License.delete().execute()
    assert License.select().count() == 0

    scraper = Scraper.create_instance('licenses')
    scraper.update_settings({"licenses-url" : "http://licenses.opendefinition.org/licenses/groups/osi.json"})
    scraper.run()

    for license in License.select():
        assert license.is_osi_compliant
