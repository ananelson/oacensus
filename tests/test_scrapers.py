from datetime import date
from oacensus.models import Journal
from oacensus.scraper import Scraper
import oacensus.load_plugins

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

def test_pubmed_scraper():
    pubmed = Scraper.create_instance('pubmed')
    settings = {
        'search' : "science[journal] AND breast cancer AND 2008[pdat]"
        }
    pubmed.update_settings(settings)
    article_list = pubmed.run()

    assert len(article_list.articles()) == 6

    for article in article_list.articles():
        assert article.title
        assert isinstance(article.date_published, date)

def test_pubmed_single_article():
    pubmed = Scraper.create_instance('pubmed')
    settings = {
        'search' : "19008416[pmid]"
        }
    pubmed.update_settings(settings)
    article_list = pubmed.run()

    assert len(article_list.articles()) == 1
    article = article_list.articles()[0]

    assert article.title == "Genomic loss of microRNA-101 leads to overexpression of histone methyltransferase EZH2 in cancer."
    assert article.date_published == date(2008, 12, 12)
    assert article.source == 'pubmed'
    assert article.pubmed_id == "19008416"
    assert article.journal.title == "Science (New York, N.Y.)"

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
