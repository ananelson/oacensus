from oacensus.scraper import Scraper
from tests.utils import setup_db

import logging
logger = logging.getLogger('peewee')
logger.setLevel(logging.WARN)

setup_db()

def test_doaj_scraper():
    limit = 2000
    scraper = Scraper.create_instance('doaj')
    scraper.update_settings({"limit" : limit})
    doaj_list = scraper.run()
    print len(doaj_list.articles())
