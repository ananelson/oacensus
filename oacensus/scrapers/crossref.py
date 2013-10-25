from oacensus.scraper import Scraper
import json
import requests
import urlparse

class Crossref(Scraper):
    """
    Gets crossref information for all articles with DOIs in the database.

    Currently this does nothing with the returned data.
    """
    aliases = ['crossref']

    _settings = {
            'base-url' : ("Base url of crossref API", "http://search.labs.crossref.org/dois")
            }

    def scrape(self):
        # don't use scrape method since our query depends on db state, so
        # caching will not be accurate
        pass

    def process(self):
        from oacensus.models import Article

        for article in Article.select():
            if not article.doi:
                continue

            response = requests.get(self.setting('base-url'),
                    params = {'q' : article.doi}
                    )
            crossref_info = json.loads(response.text)

            if crossref_info:
                # TODO get free-to-read data from CrossRef

                # parse COinS
                coins_raw_params = urlparse.urlparse(crossref_info[0]['coins']).params
                coins = urlparse.parse_qs(coins_raw_params)

                # we can get journal title but no ISSN. yay.
                journal_title = coins['rft.jtitle'][0]
                print journal_title
