from datetime import datetime
from oacensus.models import Article
from oacensus.models import ArticleList
from oacensus.scraper import Scraper
from oacensus.utils import pubmed_name
from tests.utils import setup_db
from oacensus.models import delete_all

setup_db()

def test_pubmeddoi_scraper():
    delete_all()

    dois = [
      "10.1126/science.1165395",
      "10.1371/journal.pbio.1001417",
      "10.1063/1.4818888",
      "10.1042/BST20130088"
    ]

    doilist = Scraper.create_instance("doilist")
    doilist.update_settings({
        "doi-list" : dois,
        "log" : doilist.setting("source")})
    doilist.run()

    article = Article.get(Article.doi == dois[3])
    assert article.instances.count() == 0

    pubmed = Scraper.create_instance('pubmed-update-repositories')
    pubmed.run()

    assert article.instances.count() == 2


def test_pubmed_scraper():
    delete_all()

    pubmed = Scraper.create_instance('pubmed')
    settings = {
        'search' : "science[journal] AND breast cancer",
        'start-period' : "2008-01",
        'end-period' : "2008-12"
        }
    pubmed.update_settings(settings)
    article_lists = pubmed.run()

    jan_list = article_lists[0]
    assert len(jan_list) == 2
    for article in jan_list.articles():
        assert article.period == "2008-01"
        assert article.title
        assert article.date_published == "2008-02-01"

    feb_list = article_lists[1]
    assert len(feb_list) == 2
    for article in feb_list.articles():
        assert article.period == "2008-02"
        assert article.title
        assert article.date_published == "2008-02-01"

    assert len(article_lists[2]) == 0
    assert len(article_lists[3]) == 0

    may_list = article_lists[4]
    assert len(may_list) == 1
    for article in may_list.articles():
        assert article.period == "2008-05"
        assert article.title
        assert article.date_published == "2008-05-16"

    assert len(article_lists[5]) == 0
    assert len(article_lists[6]) == 0
    assert len(article_lists[7]) == 0

    sep_list = article_lists[8]
    assert len(sep_list) == 1
    for article in sep_list.articles():
        assert article.period == "2008-09"
        assert article.title
        assert article.date_published == "2008-09-12"

    oct_list = article_lists[9]
    assert len(oct_list) == 1
    for article in oct_list.articles():
        assert article.period == "2008-10"
        assert article.title
        assert article.date_published == "2008-10-17"

    nov_list = article_lists[10]
    assert len(nov_list) == 1
    for article in nov_list.articles():
        assert article.period == "2008-11"
        assert article.title
        assert article.date_published == "2008-12-12"

    dec_list = article_lists[11]
    assert len(dec_list) == 1
    for article in dec_list.articles():
        assert article.period == "2008-12"
        assert article.title
        assert article.date_published == "2008-12-12"

    # Make another scraper over a longer time period.
    pubmed2 = Scraper.create_instance('pubmed')
    settings = {
        'search' : "science[journal] AND breast cancer",
        'start-period' : "2007-09",
        'end-period' : "2009-03",
        }
    pubmed2.update_settings(settings)

    for start_date, end_date in pubmed2.periods():
        if start_date < datetime(2008, 1, 1):
            assert not pubmed2.is_period_stored(start_date)
            assert not pubmed2.is_period_cached(start_date)
        elif start_date < datetime(2009, 1, 1):
            assert pubmed2.is_period_stored(start_date)
            assert pubmed2.is_period_cached(start_date)
        else:
            assert not pubmed2.is_period_stored(start_date)
            assert not pubmed2.is_period_cached(start_date)

    start_date = datetime(2008,2,1)
    assert Article.select().where(Article.period == "2008-02").count() == 2
    assert ArticleList.select().where(ArticleList.name == pubmed.article_list_name(start_date)).count() == 1
    assert pubmed.is_period_stored(start_date)
    pubmed.purge_period(start_date)
    assert not pubmed.is_period_stored(start_date)
    assert Article.select().where(Article.period == "2008-02").count() == 0
    assert ArticleList.select().where(ArticleList.name == pubmed.article_list_name(start_date)).count() == 0

def test_pubmed_single_article():
    pubmed = Scraper.create_instance('pubmed')
    settings = {
        'search' : "19008416[pmid]",
        'start-period' : "2008-12",
        'end-period' : "2008-12"
        }
    pubmed.update_settings(settings)
    result = pubmed.run()
    print "result is", result
    article_list = result[0]

    assert len(article_list.articles()) == 1
    article = article_list.articles()[0]

    assert article.title == "Genomic loss of microRNA-101 leads to overexpression of histone methyltransferase EZH2 in cancer."
    assert article.date_published == "2008-12-12"
    assert article.source == 'pubmed'
    assert article.period == '2008-12'
    assert article.journal.title == "Science (New York, N.Y.)"

    pubmed_instance = article.instance_for(pubmed_name)
    assert pubmed_instance.identifier == "19008416"

    pubmed.remove_stored_data()
