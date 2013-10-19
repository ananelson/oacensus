from oacensus.scraper import Scraper
from oacensus.commands import defaults

class TestScraper(Scraper):
    """
    Scraper for testing scraper methods.
    """
    aliases = ['testscraper']

    def scrape(self):
        pass

    def parse(self):
        pass

def test_hashcode():
    scraper = Scraper.create_instance('testscraper', defaults)
    assert len(scraper.hashcode()) == 32

def test_run():
    scraper = Scraper.create_instance('testscraper', defaults)
    scraper.run()
