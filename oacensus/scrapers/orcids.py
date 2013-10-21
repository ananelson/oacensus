from oacensus.models import Article
from oacensus.models import ArticleList
from oacensus.scraper import Scraper
import cPickle as pickle
import orcid
import os
import requests
import json

class OrcidOAG(Scraper):
    """
    Scrape article lists based on ORCID, then get openness info from OAG.
    """
    aliases = ['orcid']

    _settings = {
            'orcid' : ("ORCID of author to process, or a list of ORCIDS.", None),
            'oag-base-url' : ("Base url of OAG API", "http://oag.cottagelabs.com/lookup/"),
            'orcid-data-file' : ("File to save data under.", "orcid.pickle"),
            'oag-data-file' : ("File to save data under.", "oag.json"),
            'crossref-data-file' : ("File to save data under.", "crossref.json"),
            'crossref-base-url' : ("Base url of crossref API", "http://search.labs.crossref.org/dois")
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

        DOIs = [doi.id for doi, pub in self.DOIs(responses)]
        response = requests.post(self.setting('oag-base-url'), data = json.dumps(DOIs))

        oag_filepath = os.path.join(self.work_dir(), self.setting('oag-data-file'))
        with open(oag_filepath, 'w') as f:
            f.write(response.text)

        crossref_info = {}
        for doi, pub in self.DOIs(responses):
            response = requests.get(self.setting('crossref-base-url'),
                    params = {'q' : doi.id }
                    )
            crossref_info[doi.id] = json.loads(response.text)

        crossref_filepath = os.path.join(self.work_dir(), self.setting('crossref-data-file'))
        with open(crossref_filepath, 'wb') as f:
            json.dump(crossref_info, f)

    def DOIs(self, responses):
        for response in responses:
            for pub in response.publications:
                if pub.external_ids:
                    for ext_id in pub.external_ids:
                        if ext_id.type == "DOI":
                            yield (ext_id, pub)

    def parse_single_orcid_response(self, response, license_info, crossref_info):
        args = (response.orcid, response.given_name, response.family_name)
        list_name = "ORCID %s  Author: %s %s" % args
        article_list = ArticleList.create(name = list_name, orcid = response.orcid)

        for doi, pub in self.DOIs([response]):
            license = license_info[doi.id]

            #crossref = crossref_info[doi.id]
            #if crossref:
            #    crossref[0].keys()
            #    # [u'normalizedScore', u'doi', u'title',
            #       u'coins', u'fullCitation', u'score', u'year']

            article = Article.create_or_update_by_doi({
                'doi' : doi,
                'title' : pub.title,
                'open_access' : license[0]['open_access'],
                'license' : license[0]['title'].strip()
                })

            article_list.add_article(article)

        return article_list

    def parse(self):
        orcid_filepath = os.path.join(self.cache_dir(), self.setting('orcid-data-file'))
        with open(orcid_filepath, 'rb') as f:
            responses = pickle.load(f)

        oag_filepath = os.path.join(self.cache_dir(), self.setting('oag-data-file'))
        with open(oag_filepath, 'rb') as f:
            oag_response = json.load(f)

        license_info_by_doi = {}
        for oag_result in oag_response['results']:
            license_info_by_doi[oag_result['identifier'][0]['id']] = oag_result['license']

        crossref_filepath = os.path.join(self.cache_dir(), self.setting('crossref-data-file'))
        with open(crossref_filepath, 'rb') as f:
            crossref_info = json.load(f)

        for response in responses:
            print self.parse_single_orcid_response(response,
                    license_info_by_doi, crossref_info)
