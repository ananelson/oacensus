from oacensus.commands import defaults
from oacensus.scraper import Scraper
from datetime import date

def test_pubmed_scraper():
    pubmed = Scraper.create_instance('pubmed', defaults)
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
    pubmed = Scraper.create_instance('pubmed', defaults)
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
