from oacensus.exceptions import APIError
from oacensus.models import Article
from oacensus.models import ArticleList
from oacensus.models import Journal
from oacensus.scraper import ArticleScraper
import dateutil.parser
import os
import requests
import time
import xml.etree.ElementTree as ET

class NCBI(ArticleScraper):
    """
    Base class for scrapers querying NCBI databases (including pubmed).
    """
    aliases = []
    _settings = {
            "base-url" : ("Base url of API.", "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/"),
            "ncbi-db" : ("Name of NCBI database to query.", None),
            "search" : ("Search query to include.", None),
            "datetype" : ("Type of date for period filtering", "pdat"),
            "filepattern" : ("Names of files which hold data in cache.", "data_%04d.xml"),
            "ret-max" : ("Maximum number of entries to return in any single query.", 10000),
            "delay" : ("Time in seconds to delay between API requests.", 1),
            "initial-ret-max" : ("Maximum number of entries to return in the initial query.", 5)
        }

    def search_url(self):
        """
        URL for the Search API, which returns UIDs of articles matching the
        search query.
        """
        return "%s/esearch.fcgi" % self.setting('base-url')

    def fetch_url(self):
        """
        URL for the Fetch API, which returns full records of articles.
        """
        return "%s/efetch.fcgi" % self.setting('base-url')

    def search_params(self, override_params=None):
        universal_default_params = {
                'db' : self.setting('ncbi-db'),
                'retMax' : self.setting('ret-max'),
                }

        universal_default_params.update(override_params)
        return universal_default_params

    def initial_search_with_period(self, start_date, end_date):
        """
        Method which implements the initial search.

        Returns a count of records, a WebEnv value and a QueryKey value which
        will be used to fetch the full results.
        """
        params = {
                'term' : self.setting('search'),
                'usehistory' : 'y',
                'datetype' : self.setting('datetype'),
                'mindate' : start_date.strftime("%Y/%m/%d"),
                'maxdate' : end_date.strftime("%Y/%m/%d"), # TODO is this right?
                'retMax' : self.setting('initial-ret-max')
                }

        result = requests.get(
                self.search_url(),
                params=self.search_params(params)
                )

        root = ET.fromstring(result.text)
    
        error = root.find("ERROR")
        if error is not None:
            raise APIError(error.text)

        count = int(root.find("Count").text)
        web_env = root.find("WebEnv").text
        query_key = root.find("QueryKey").text

        args = (count, start_date, end_date)
        self.print_progress("  there are %s total articles matching the search between %s and %s" % args)

        return (count, web_env, query_key)

    def data_filepath(self, i, start_date):
        return os.path.join(self.period_work_dir(start_date), self.setting('filepattern') % i)

    def fetch_batch(self, i, retstart, retmax, web_env, query_key, start_date):
        self.print_progress("waiting requested delay time...")
        time.sleep(self.setting('delay'))
        msg = "fetching values %s through %s..." % (retstart, retstart+retmax-1)
        self.print_progress(msg)

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

        work_file = self.data_filepath(i, start_date)
        self.print_progress("saving data to %s" % work_file)
        with open(work_file, "wb") as f:
            for block in result.iter_content(1024):
                if not block:
                    break
                f.write(block)

    def scrape_period(self, start_date, end_date):
        count, web_env, query_key = self.initial_search_with_period(start_date, end_date)

        i = 0
        retstart = 0
        retmax = self.setting('ret-max')

        while retstart < count:
            self.fetch_batch(i, retstart, retmax, web_env, query_key, start_date)
            retstart += retmax
            i += 1

    def parse_date(self, entry):
        if entry is not None:
            year = entry.findtext("Year")
            month = entry.findtext("Month")
            day = entry.findtext("Day")

            if day is None:
                day = "1"

            if month is None:
                month = "1"

            if year is not None:
                datestring = '%s %s %s' % (year, month, day)
                return dateutil.parser.parse(datestring)

class Pubmed(NCBI):
    """
    Creates a single ArticleList and individual Article objects for all
    articles returned from pubmed matching the [required] search query.
    """
    aliases = ['pubmed']
    _settings = {
            "ncbi-db" : "pubmed"
            }

    def purge_period(self, start_date):
        ArticleList.delete().where(ArticleList.name == self.article_list_name(start_date)).execute()
        Article.delete().where(Article.period == start_date.strftime("%Y-%m")).execute()

    def article_list_name(self, start_date):
        list_args = (self.setting('search'), start_date.strftime("%Y-%m"))
        return "pubmed search: %s %s" % list_args

    def is_period_stored(self, start_date):
        try:
            ArticleList.get(ArticleList.name == self.article_list_name(start_date))
            return True
        except ArticleList.DoesNotExist:
            return False

    def process_period(self, start_date, end_date):
        article_list = ArticleList.create(
            name=self.article_list_name(start_date))

        cache_dir = self.period_cache_dir(start_date)
        for filename in os.listdir(cache_dir):
            filepath = os.path.join(cache_dir, filename)
            with open(filepath, 'rb') as f:
                tree = ET.parse(f)
                root = tree.getroot()
                assert root.tag == "PubmedArticleSet"
                for pubmed_article in root:
                    assert pubmed_article.tag == "PubmedArticle"

                    medline_citation = pubmed_article.find("MedlineCitation")
                    article_entry = medline_citation.find("Article")
                    journal_entry = article_entry.find("Journal")

                    # Parse journal info
                    journal_title = journal_entry.findtext("Title")
                    journal_iso = journal_entry.findtext("ISOAbbreviation")
                    issn_entry = journal_entry.find("ISSN")

                    if issn_entry is None:
                        issn = journal_iso
                    else:
                        issn = issn_entry.text

                    journal = Journal.create_or_update_by_issn({
                        'issn' : issn,
                        'title' : journal_title,
                        'source' : self.alias
                        })

                    # Parse article info
                    title = article_entry.findtext("ArticleTitle")

                    # Parse date info
                    date_published = None
                    journal_pubdate_entry = journal_entry.find("JournalIssue").find("PubDate")
                    article_date_entry = article_entry.find("ArticleDate")

                    if journal_pubdate_entry is not None:
                        date_published = self.parse_date(journal_pubdate_entry)
                    elif article_date_entry is not None:
                        date_published = self.parse_date(article_date_entry)

                    doi_entry = article_entry.find("ELocationID")

                    doi = None
                    if doi_entry is not None:
                        eid_type = doi_entry.get("EIdType")
                        if eid_type == 'doi':
                            doi = doi_entry.text

                    pubmed_id = medline_citation.findtext("PMID")

                    nihm_id = None
                    pcm_id = None
                    for other_id in medline_citation.findall("OtherID"):
                        other_id_text = other_id.text
                        if other_id_text.startswith("NIHM"):
                            nihm_id = other_id_text
                        elif other_id_text.startswith("PMC"):
                            pcm_id = other_id_text
                        else:
                            pass

                    assert title is not None

                    article = Article.create(
                            title = title,
                            source = self.alias,
                            doi = doi,
                            journal = journal,
                            period = start_date.strftime("%Y-%m"),
                            date_published = date_published,
                            pubmed_id = pubmed_id,
                            nihm_id = nihm_id,
                            pcm_id = pcm_id
                            )

                    article_list.add_article(article)

        self.print_progress("  %s" % article_list)
        return article_list
