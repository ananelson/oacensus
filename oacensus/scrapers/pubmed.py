from oacensus.models import Article
from oacensus.scraper import Scraper
import datetime
import os
import requests
import time
import xml.etree.ElementTree as ET

class NCBIScraper(Scraper):
    """
    Scraper for NCBI resources, including pubmed.
    """
    aliases = ['ncbi', 'pubmed']
    _settings = {
            "base-url" : ("Base url of API.", "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/"),
            "ncbi-db" : ("Name of NCBI database to query.", "pubmed"),
            "search-term" : ("Search query to include.", None),
            "filepattern" : (
                "Pattern to use for names of files which hold data in cache.",
                "data_%04d.xml"
                ),
            "ret-max" : ("Maximum number of entries to return in any single query.", 10000),
            "delay" : ("Time in seconds to delay between API requests.", 1),
            "initial-ret-max" : ("Maximum number of entries to return in the initial query.", 5)
            }

    def search_url(self):
        """
        Search API returns UIDs of articles matching the search query.
        """
        return "%s/esearch.fcgi" % self.setting('base-url')

    def fetch_url(self):
        """
        Fetch API returns full records of articles.
        """
        return "%s/efetch.fcgi" % self.setting('base-url')

    def search_params(self, extra_params=None):
        params = {
                'db' : self.setting('ncbi-db'),
                'retMax' : self.setting('ret-max'),
                }

        params.update(extra_params)
        return params

    def initial_search(self):
        """
        Method which implements the initial search.

        Returns a count of records, a WebEnv value and a QueryKey value which
        will be used to fetch the full results.
        """
        params = {
                'term' : self.setting('search-term'),
                'usehistory' : 'y',
                'retMax' : self.setting('initial-ret-max')
                }

        result = requests.get(
                self.search_url(),
                params=self.search_params(params)
                )

        root = ET.fromstring(result.text)

        count = int(root.find("Count").text)
        web_env = root.find("WebEnv").text
        query_key = root.find("QueryKey").text

        print "There are %s total articles matching the search." % count

        return (count, web_env, query_key)

    def data_filepath(self, i):
        return os.path.join(self.work_dir(), self.setting('filepattern') % i)

    def fetch_batch(self, i, retstart, retmax, web_env, query_key):
        print "waiting requested delay time..."
        time.sleep(self.setting('delay'))
        print "fetching values %s through %s..." % (retstart, retstart+retmax-1)

        params = {
                'WebEnv' : web_env,
                'query_key' : query_key,
                'RetStart' : retstart,
                'usehistory' : 'y',
                'retmode' : 'xml'
                }

        result = requests.get(
                self.fetch_url(),
                params=self.search_params(params),
                stream=True
                )

        with open(self.data_filepath(i), "wb") as f:
            for block in result.iter_content(1024):
                if not block:
                    break
                f.write(block)

    def scrape(self):
        count, web_env, query_key = self.initial_search()

        i = 0
        retstart = 0
        retmax = self.setting('ret-max')

        while retstart < count:
            self.fetch_batch(i, retstart, retmax, web_env, query_key)
            retstart += retmax
            i += 1

    def parse_date(self, entry):
        if entry is not None:
            return datetime.date(
                int(entry.findtext('Year')),
                int(entry.findtext('Month')),
                int(entry.findtext('Day'))
                )

    def parse(self):
        for filename in os.listdir(self.cache_dir()):
            filepath = os.path.join(self.cache_dir(), filename)
            with open(filepath, 'rb') as f:
                tree = ET.parse(f)
                root = tree.getroot()
                assert root.tag == "PubmedArticleSet"
                for pubmed_article in root:
                    assert pubmed_article.tag == "PubmedArticle"

                    pubmed_data = pubmed_article.find("PubmedData")
                    medline_citation = pubmed_article.find("MedlineCitation")
                    article_entry = medline_citation.find("Article")
                    journal_entry = article_entry.find("Journal")

                    assert pubmed_data is not None
                    assert medline_citation is not None
                    assert article_entry is not None
                    assert journal_entry is not None

                    article = Article()
                    article.pubmed_id = medline_citation.findtext("PMID")
                    article.title = article_entry.findtext("ArticleTitle")
                    article.date_published = self.parse_date(article_entry.find("ArticleDate"))
                    article.date_created = self.parse_date(medline_citation.find("DateCreated"))
                    article.date_completed = self.parse_date(medline_citation.find("DateCompleted"))

                    for other_id in medline_citation.findall("OtherID"):
                        other_id_text = other_id.text
                        if other_id_text.startswith("NIHM"):
                            article.nihm_id = other_id_text
                        elif other_id_text.startswith("PMC"):
                            article.pcm_id = other_id_text
                        else:
                            raise Exception("Unrecognized other id '%s'" % other_id_text)

                    article.save()

class BreastCancerQuery(NCBIScraper):
    """
    Example query which returns small number of results.
    """
    aliases = ['bc']
    _settings = {
            'search-term' : "science[journal] AND breast cancer AND 2008[pdat]"
            }
