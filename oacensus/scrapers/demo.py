from oacensus.scraper import Scraper
from oacensus.models import Publisher
import os

class Demo(Scraper):
    """
    A scraper for demonstrating and documenting features of scrapers. Does not
    need to connect to the internet.
    """
    aliases = ['demo']

    _settings = {
            "data-file" : ("file to save data under", "data.txt"),
            }

    def scrape(self):
        filepath = os.path.join(self.work_dir(), self.setting('data-file'))
        data = "foo bar baz"
        with open(filepath, 'w') as f:
            f.write(data)

    def process(self):
        filepath = os.path.join(self.cache_dir(), self.setting('data-file'))
        with open(filepath, 'r') as f:
            raw_data = f.read()
        publisher_names = raw_data.split()
        for name in publisher_names:
            Publisher.create(name=name, source=self.db_source())
