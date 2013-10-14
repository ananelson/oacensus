from oacensus.scraper import Scraper
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
        return os.path.join(self.work_dir(), "data_%04d.xml" % i)

    def fetch_batch(self, i, retstart, retmax, web_env, query_key):
        print "waiting..."
        time.sleep(self.setting('delay'))
        print "Fetching values %s through %s..." % (retstart, retstart+retmax-1)

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

    def parse(self):
        pass
