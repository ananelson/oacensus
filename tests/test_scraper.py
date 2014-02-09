from oacensus.scraper import Scraper
from oacensus.commands import defaults
from datetime import datetime
from dateutil import relativedelta

class TestScraper(Scraper):
    """
    Scraper for testing scraper methods.
    """
    aliases = ['testscraper']

    def scrape(self):
        pass

    def process(self):
        pass

def test_hashcode():
    scraper = Scraper.create_instance('testscraper', defaults)
    assert len(scraper.hashcode(scraper.hash_settings())) == 32

def test_run():
    scraper = Scraper.create_instance('testscraper', defaults)
    scraper.run()

def make_article_scraper(overrides = None):
    scraper = Scraper.create_instance('articlescraper', defaults)
    settings = {"start-month" : "2010-01", "end-month" : "2010-12"}
    if overrides:
        settings.update(overrides)
    scraper.update_settings(settings)
    return scraper

def test_no_end_month_is_ok():
    scraper = make_article_scraper({
        "end-month" : None
        })

    periods = [p for p in scraper.periods()]
    assert periods[-1] < datetime.now()
    assert periods[-1] > datetime.now() + relativedelta.relativedelta(months = -2)

def test_invalid_end_month_before_start_month():
    scraper = make_article_scraper({
        "end-month" : "2009-12"
        })

    try:
        scraper.periods()
        assert False, "should not be here"
    except Exception as e:
        assert "must be before" in str(e)

def test_invalid_end_month_after_today():
    this_month = datetime.today().strftime("%Y-%m")
    scraper = make_article_scraper({
        "end-month" : this_month
        })

    try:
        scraper.periods()
        assert False, "should not be here"
    except Exception as e:
        print str(e)
        assert "before the current date" in str(e)

def test_article_scraper_periods():
    scraper = make_article_scraper()
    periods = [p for p in scraper.periods()]
    assert len(periods) == 12
    assert periods[0] == datetime(2010,1,1)
    assert periods[11] == datetime(2010,12,1)

def test_article_scraper_period_hashes():
    scraper = make_article_scraper()
    for period in scraper.periods():
        hash_settings = scraper.period_hash_settings(period)
        assert hash_settings['period'].startswith("2010-")
        assert len(scraper.period_hashcode(period)) == 32
