from oacensus.models import Article
from oacensus.models import Instance
from oacensus.models import License
from oacensus.models import Repository
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
            'max-items' : ("Maximum number of items in a single API request.", 1000),
            'repository-name' : ("Name of OAG repository.", "Open Article Gauge")
            }

    def scrape(self):
        pass

    def create_repository(self):
        return Repository.create(
                name = self.setting('repository-name'),
                source = self.db_source(),
                log = self.db_source())

    def process(self):
        articles_with_dois = Article.select().where(~(Article.doi >> None))
        repository = self.create_repository()

        api_url = self.setting('base-url')
        max_items = self.setting('max-items')
        n_articles = articles_with_dois.count()
        n_batches = n_articles/max_items+1

        for i in range(n_batches):
            self.print_progress("Processing query %s of %s" % (i+1, n_batches))
            articles = articles_with_dois.paginate(i, paginate_by=max_items)
            dois = [article.doi for article in articles]

            response = requests.post(api_url, data = json.dumps(dois))
            oag_response = json.loads(response.text)['results']

            oag_response_map = dict((v['identifier'][0]['id'], v) for v in oag_response)

            for article in articles:
                oag_info = oag_response_map[article.doi]

                for license_info in oag_info['license']:

                    if license_info['type'] == "failed-to-obtain-license":
                        article.log += "\nOAG attempted but failed to obtain license information."

                    elif license_info['type'] == "free-to-read":
                        Instance.create(
                                article=article,
                                repository=repository,
                                free_to_read = True,
                                source=self.db_source(),
                                log=license_info['provenance']['description'])

                    else:
                        alias = license_info['type']
                        license = License.find_license(alias)
                        Instance.create(
                                article=article,
                                repository=repository,
                                license=license,
                                free_to_read = True,
                                source=self.db_source(),
                                log=license_info['provenance']['description'])
