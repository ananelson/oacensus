from oacensus.commands import defaults
from oacensus.scraper import Scraper
from oacensus.models import Article
from datetime import date

def test_pubmed_scraper():
    pubmed = Scraper.create_instance('pubmed', defaults)
    settings = {
        'search' : "science[journal] AND breast cancer AND 2008[pdat]"
        }
    pubmed.update_settings(settings)
    pubmed.run()

    assert Article.select().count() == 6

    for article in Article.select():
        assert article.title
        assert isinstance(article.date_published, date)
