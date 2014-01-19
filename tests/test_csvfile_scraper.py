from oacensus.commands import defaults
from oacensus.scraper import Scraper
import datetime

import oacensus.load_plugins

from oacensus.models import create_db_tables
from oacensus.db import db
db.init(":memory:")
create_db_tables()

def test_scrape():
    list_name = "Test List"
    csv = Scraper.create_instance('csvfile', defaults)
    csv.update_settings({
        'csv-file' : 'tests/test.csv',
        'list-name' : list_name,
        'column-mapping' : {
            "DOI" : 'doi',
            "ISSN" : 'journal.issn',
            "Publication Date" : 'date_published',
            "Article Title" : 'title',
            "Journal Title" : 'journal.title'
        }
    })
    article_list = csv.run()
    assert len(article_list) == 100
    assert article_list.name == list_name

    article = article_list.articles()[0]
    assert article.date_published == datetime.date(2008,1,1)
    assert article.journal.title == "Logical Methods in Computer Science"
    assert article.journal.issn == "1860-5974"

    article = article_list.articles()[1]
    assert article.date_published == datetime.date(2008,3,1)

    article = article_list.articles()[10]
    assert article.date_published == datetime.date(2009,1,12)
