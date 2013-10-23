from oacensus.scraper import Scraper
import cPickle as pickle
import orcid
import os

class Orcid(Scraper):
    """
    Generate lists of articles for authors based on ORCID.
    """
    aliases = ['orcid']

    _settings = {
            'orcid' : ("ORCID of author to process, or a list of ORCIDS.", None),
            'orcid-data-file' : ("File to save data under.", "orcid.pickle")
            }

    def scrape(self):
        if not self.setting('orcid'):
            raise Exception("Must provide an ORCID.")

        if isinstance(self.setting('orcid'), basestring):
            orcids = [self.setting('orcid')]
        else:
            orcids = self.setting('orcid')

        responses = [orcid.get(orcd) for orcd in orcids]

        orcid_filepath = os.path.join(self.work_dir(), self.setting('orcid-data-file'))
        with open(orcid_filepath, 'wb') as f:
            pickle.dump(responses, f)

    def parse(self):
        from oacensus.models import Article
        from oacensus.models import ArticleList

        orcid_filepath = os.path.join(self.cache_dir(), self.setting('orcid-data-file'))
        with open(orcid_filepath, 'rb') as f:
            responses = pickle.load(f)

        for response in responses:
            args = (response.orcid, response.given_name, response.family_name)
            list_name = "ORCID %s  Author: %s %s" % args
            article_list = ArticleList.create(name = list_name, orcid = response.orcid)

            for pub in response.publications:
                doi = None
                if pub.external_ids:
                    for ext_id in pub.external_ids:
                        if ext_id.type == "DOI":
                            doi = ext_id.id

                article = Article.create_or_update_by_doi({
                    'source' : self.alias,
                    'doi' : doi,
                    'url' : pub.url,
                    'title' : pub.title
                    })

                article_list.add_article(article)

            return article_list
