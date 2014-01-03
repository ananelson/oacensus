from oacensus.commands import defaults
from oacensus.scraper import Scraper
from datetime import date
import re

def test_scrape():
    csv = Scraper.create_instance('csvfile', defaults)
    csv.update_settings(
                        {
                        'csv-file' : 'test.csv',
                        }
                       )

    csv.scrape()


