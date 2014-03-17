from oacensus.scraper import Scraper
from tests.utils import setup_db
import oacensus.load_plugins
from oacensus.models import delete_all

setup_db()

def test_crossref_journal_titles_scraper():

    crossref = Scraper.create_instance("crossrefjournals")
    crossref.update_settings({
        'limit' : 5,
        'add-new-journals' : True
        })

    crossref_list = crossref.run()

    print crossref_list
    for journal in crossref_list.journals():
        print journal

    assert len(crossref_list) == 5

def test_crossref_scraper():
    crossref = Scraper.create_instance("crossref")
    crossref.run()
