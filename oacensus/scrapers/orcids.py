from oacensus.models import Article
from oacensus.models import ArticleList
from oacensus.scraper import Scraper
import cPickle as pickle
import orcid
import os

class Orcid(Scraper):
    """
    Scrape article lists based on ORCID.
    """
    aliases = ['orcid']

    _settings = {
            'orcid' : ("ORCID of author to process, or a list of ORCIDS.", None),
            'base-url' : ("Base url", "http://pub.orcid.org/"),
            'data-file' : ("File to save data under.", "orcid.pickle")
            }

    def scrape(self):
        if not self.setting('orcid'):
            raise Exception("Must provide an ORCID.")


        if isinstance(self.setting('orcid'), basestring):
            orcids = [self.setting('orcid')]
        else:
            orcids = self.setting('orcid')

        responses = [orcid.get(orcd) for orcd in orcids]

        filepath = os.path.join(self.work_dir(), self.setting('data-file'))
        with open(filepath, 'wb') as f:
            pickle.dump(responses, f)

    def parse_single_orcid_response(self, response):
        args = (response.orcid, response.given_name, response.family_name)
        list_name = "ORCID %s  Author: %s %s" % args
        article_list = ArticleList.create(name = list_name) 

        for pub in response.publications:
            if pub.external_ids:
                for ext_id in pub.external_ids:
                    if ext_id.type == "DOI":
                        article = Article.create_or_update_by_doi({
                            'doi' : ext_id,
                            'title' : pub.title
                            })

            article_list.add_article(article)

        return article_list

    def parse(self):
        filepath = os.path.join(self.cache_dir(), self.setting('data-file'))

        with open(filepath, 'rb') as f:
            responses = pickle.load(f)

        for response in responses:
            print self.parse_single_orcid_response(response)
