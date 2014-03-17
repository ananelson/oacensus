from oacensus.scraper import Scraper
from oacensus.models import Article
from tests.utils import setup_db
import oacensus.load_plugins
from oacensus.models import delete_all

setup_db()

def test_orcid_scraper():
    delete_all()
    orcid = "0000-0002-0068-716X"

    scraper = Scraper.create_instance("orcid")
    scraper.update_settings({
        "orcid" : orcid
        })

    assert Article.select().count() == 0

    scraper.run()

    assert Article.select().count() > 50

