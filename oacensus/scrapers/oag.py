from oacensus.models import Article
from oacensus.scraper import Scraper
import json
import requests


class OAG(Scraper):
    """
    Adds information from Open Article Gauge (OAG) to articles.

    Requests information from the OAG API for each article in the oacensus
    database which has a DOI (articles must already be populated from some
    other source).
    """
    aliases = ['oag']

    _settings = {
            'base-url' : ("Base url of OAG API", "http://oag.cottagelabs.com/lookup/"),
            'max-items' : ("Maximum number of items in a single API request.", 1000)
            }

    def process(self):
        api_url = self.setting('base-url')
        max_items = self.setting('max-items')
        n_articles = Article.select().count()
        n_batches = n_articles/max_items+1

        for i in range(n_batches):
            self.print_progress("Processing query number %s of %s" % (i, n_batches))
            articles = Article.select().where(Article.doi).paginate(i, paginate_by=max_items)
            dois = [article.doi for article in articles]

            response = requests.post(api_url, data = json.dumps(dois))
            oag_response = json.loads(response.text) 

            # Make a map using DOIs as keys to easily look up license info later.
            license_info_by_doi = {}
            for oag_result in oag_response['results']:
                license_info_by_doi[oag_result['identifier'][0]['id']] = oag_result['license']

            for article in articles:
                license = license_info_by_doi.get(article.doi)

                if not license:
                    print "  no license info returned for", article
                    continue

                self.update_article_with_license_info(article, license)

    def update_article_with_license_info(self, article, license):
        article.open_access = license[0]['open_access']
        article.open_access_source = self.alias
        article.license = license[0]['title'].strip()
        article.save()
