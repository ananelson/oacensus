from datetime import date
from oacensus.models import Journal
from oacensus.scraper import Scraper
from tests.utils import setup_db
import oacensus.load_plugins

setup_db()

def test_crossref_titles_scraper():
    crossref = Scraper.create_instance("crossrefjournals")
    crossref.update_settings({
        'limit' : 5,
        'add-new-journals' : True
        })

    crossref_list = crossref.run()
    assert len(crossref_list) == 5

## Article scrapers

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

# Article Info scrapers
def test_crossref_scraper():
    crossref = Scraper.create_instance("crossref")
    crossref.run()

# Journal scrapers
def test_biomed_scraper():
    biomed = Scraper.create_instance('biomed')
    biomed.update_settings({ "limit" : 2 })
    biomed_list = biomed.run()

    print "length of biomed_list", len(biomed_list)
    assert len(biomed_list) == 2

    for journal in biomed_list:
        assert journal.source == "biomed"
        assert journal.open_access
        assert "creativecommons.org" in journal.license 

def test_doaj_scraper():
    limit = 5
    doaj = Scraper.create_instance('doaj')
    doaj.update_settings({
        "limit" : limit,
        "add-new-journals" : True
        })
    doaj_list = doaj.run()

    assert len(doaj_list) == limit

    journals = Journal.select().where(Journal.open_access_source == "doaj")
    for journal in journals:
        assert journal.license.startswith("CC-")
