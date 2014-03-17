from oacensus.scraper import Scraper
from tests.utils import setup_db
import oacensus.load_plugins
from nose.exc import SkipTest

setup_db()

def test_elsevier_scraper():
    raise SkipTest()
    scraper = Scraper.create_instance("elsevier")
    scraper.update_settings({
        'pages' : ["a"]
        })
    scraper.run()
