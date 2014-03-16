from oacensus.models import Journal
from oacensus.scraper import Scraper
from tests.utils import setup_db
import oacensus.load_plugins

setup_db()

def test_biomed_scraper():
    limit = 3
    biomed = Scraper.create_instance('biomed')
    biomed.update_settings({ "limit" : limit })
    biomed_list = biomed.run()

    assert len(biomed_list) == limit

    for journal in biomed_list:
        assert journal.source == "biomed"
        assert journal.is_free_to_read()
        assert journal.ratings[0].license.title == "Creative Commons Attribution"
