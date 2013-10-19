from oacensus.commands import defaults
from oacensus.scraper import Scraper

def test_pubmed_scraper():
    pubmed = Scraper.create_instance('pubmed', defaults)
    settings = {
        'search-term' : "science[journal] AND breast cancer AND 2008[pdat]"
        }
    pubmed.update_settings(settings)
    pubmed.run()
