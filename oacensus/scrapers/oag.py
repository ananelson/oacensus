from oacensus.scraper import Scraper
import json
import requests

class OAG(Scraper):
    """
    Gets license information for all articles with DOIs in the database.
    """
    aliases = ['oag']

    _settings = {
            'base-url' : ("Base url of OAG API", "http://oag.cottagelabs.com/lookup/"),
            }

    def scrape(self):
        # don't use scrape method since our query depends on db state, so
        # caching will not be accurate
        pass

    def process(self):
        from oacensus.models import Article
        articles = Article.select()
        DOIs = [article.doi for article in articles if article.doi]
        response = requests.post(self.setting('base-url'), data = json.dumps(DOIs))
        oag_response = json.loads(response.text) 

        license_info_by_doi = {}
        for oag_result in oag_response['results']:
            license_info_by_doi[oag_result['identifier'][0]['id']] = oag_result['license']

        for article in articles:
            if not article.doi:
                continue
            
            license = license_info_by_doi.get(article.doi)
            if not license:
                print "  no info found for", article
                continue

            article.open_access = license[0]['open_access']
            article.open_access_source = self.alias
            article.license = license[0]['title'].strip()
            article.save()
