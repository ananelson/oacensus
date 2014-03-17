from oacensus.scraper import Scraper
from oacensus.models import Article
from tests.utils import setup_db
import oacensus.load_plugins

setup_db()

def test_oag_scraper():
    dois = [
      "http://dx.doi.org/10.1126/science.1165395",
      "http://dx.doi.org/10.1371/journal.pbio.1001417"
    ]

    doilist = Scraper.create_instance("doilist")
    doilist.update_settings({"doi-list" : dois })
    doilist.run()

    scraper = Scraper.create_instance("oag")
    scraper.run()

    a1 = Article.select().where(Article.doi == dois[0])[0]
    assert a1.instances[0].license == None

    a2 = Article.select().where(Article.doi == dois[1])[0]
    assert a2.instances[0].license.title == "Creative Commons Attribution"
