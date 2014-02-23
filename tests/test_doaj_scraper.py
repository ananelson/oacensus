from oacensus.scraper import Scraper
from tests.utils import setup_db

setup_db()

def test_doaj_scraper():
    scraper = Scraper.create_instance('doaj')
    scraper.update_settings({"limit" : 1000})
    scraper.run()
