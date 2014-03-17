from oacensus.scraper import Scraper
from oacensus.scraper import Rating
from tests.utils import setup_db

import logging
logger = logging.getLogger('peewee')
logger.setLevel(logging.WARN)

setup_db()

def test_doaj_scraper():
    limit = 2000 # Should be large enough to hit special cases
    scraper = Scraper.create_instance('doaj')
    scraper.update_settings({"limit" : limit})
    scraper.run()

    ratings = Rating.select().where(Rating.source == scraper.alias)
    assert ratings.count() == limit
    
    rating = ratings[0]
    assert rating.free_to_read
    assert rating.journal.is_free_to_read()
