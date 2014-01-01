from oacensus.models import Article
from oacensus.models import ArticleList
from oacensus.scraper import ArticleScraper
from oacensus.utils import parse_crossref_coins
import json
import os
import requests

class DOIList(ArticleScraper):
    """
    Reads a list of DOIs from an external source. Uses crossref (currently) to retrieve metadata.
    """
    aliases = ['doilist']

    _settings = {
            'base-url' : ("Base url of crossref API", "http://search.labs.crossref.org/dois"),
            "doi-file" : ("Path to file containing list of DOIs.", "dois.txt"),
            "doi-list" : ("Specify list of DOIs directly instead of via a file.", None),
            "list-name" : ("Custom list name.", "Custom DOI List"),
            "data-file" : ("Name of cache file to store DOIs.", "work.txt"),
            "source" : ("'source' attribute to use for articles.", "doilist")
            }

    def scrape(self):
        """
        Assume the DOIs are separated by whitespace (tabs, spaces or newlines).
        Subclass this to implement other parsers which read from a local file
        and extract DOIs.
        """
        if self.setting('doi-list') is not None:
            DOIs = self.setting('doi-list')
        else:
            with open(self.setting('doi-file'), 'r') as f:
                data = f.read()
                DOIs = [datum.strip() for datum in data.split()]

        data_file = os.path.join(self.work_dir(), self.setting('data-file'))
        with open(data_file, 'wb') as f:
            json.dump(DOIs, f)

    def process(self):
        data_file = os.path.join(self.cache_dir(), self.setting('data-file'))
        with open(data_file, 'rb') as f:
            DOIs = json.load(f)

        article_list = ArticleList.create(name=self.setting('list-name'))

        for doi in DOIs:
            response = requests.get(self.setting('base-url'),
                    params = {'q' : doi}
                    )
            response_list = json.loads(response.text)

            if len(response_list) == 0:
                print "No responses matched doi %s, skipping." % doi
            elif len(response_list) > 1:
                print "Multiple responses matched doi %s, skipping." % doi
            else:
                crossref_info = response_list[0]
                coins = parse_crossref_coins(crossref_info)

                print coins.keys()
                print coins
                print crossref_info.keys()

                article = Article.create(
                        title = crossref_info['title'],
                        doi = doi,
                        source = self.setting('source')
                        )

                #print article
                article_list.add_article(article)

        print "  ", article_list
        return article_list
