from oacensus.scraper import Scraper
import datetime

from tests.utils import setup_db
setup_db()

def test_scrape():
    list_name = "Articles From a CSV File"
    source = "custom-article-list"
    scraper = Scraper.create_instance('csvarticles')
    scraper.update_settings({
        'location' : 'tests/test.csv',
        "list-name" : list_name,
        'source' : source,
        "period" : "unknown",
        'column-mapping' : {
            "DOI" : 'doi',
            "ISSN" : 'journal.issn',
            "Publication Date" : 'date_published',
            "Article Title" : 'title',
            "Journal Title" : 'journal.title'
        }
    })
    article_list = scraper.run()
    assert len(article_list) == 100
    assert article_list.name == list_name
    assert article_list.source == source

    article = article_list.articles()[0]
    assert article.date_published == datetime.date(2008,1,1)
    assert article.journal.title == "Logical Methods in Computer Science"
    assert article.journal.issn == "1860-5974"
    assert article.source == source
    assert article.journal.source == source

    article = article_list.articles()[1]
    assert article.date_published == datetime.date(2008,3,1)

    article = article_list.articles()[10]
    assert article.date_published == datetime.date(2009,1,12)
