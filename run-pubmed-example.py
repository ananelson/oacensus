import oacensus.load_scrapers

from oacensus.scraper import Scraper

settings = {
        'search-term' : "science[journal] AND breast cancer AND 2008[pdat]"
        }

pubmed = Scraper.create_instance('pubmed')
pubmed.update_settings(settings)

pubmed.run()
