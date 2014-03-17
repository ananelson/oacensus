from oacensus.scraper import Scraper
from tests.utils import setup_db
import oacensus.load_plugins

setup_db()

def test_doilist_scraper():
    doilist = Scraper.create_instance("doilist")
    doilist.update_settings({
        "doi-list" : ["http://dx.doi.org/10.1126/science.1165395"],
        "list-name" : "My Custom List"
        })
    article_list = doilist.run()
    article = article_list[0]

    assert article_list.name == "My Custom List"
    assert article.source == 'doilist'
