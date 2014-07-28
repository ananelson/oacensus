from bs4 import BeautifulSoup
from oacensus.exceptions import APIError
from oacensus.models import Article
from oacensus.models import ArticleList
from oacensus.models import Instance
from oacensus.models import Journal
from oacensus.models import Repository
from oacensus.models import pubmed_external_ids
from oacensus.scraper import ArticleScraper
from oacensus.scraper import Scraper
import datetime
import dateutil.parser
import os
import requests
import time
import xml.etree.ElementTree as ET

# TODO remove these and use pubmed_external_ids
from oacensus.utils import nihm_name, pmc_name, pubmed_name

class NCBI(Scraper):
    """
    Base class for scrapers querying NCBI databases (including pubmed).
    """
    aliases = ['ncbibase']
    _settings = {
            "base-url" : ("Base url of API.", "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/"),
            "ncbi-db" : ("Name of NCBI database to query.", None),
            "datetype" : ("Type of date for period filtering", "pdat"),
            "filepattern" : ("Names of files which hold data in cache.", "data_%04d.xml"),
            "ret-max" : ("Maximum number of entries to return in any single query.", 500),
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

    def search_params(self, provided_params=None):
        """
        Standardizes params and provides universal defaults.
        """
        if self.setting('ncbi-db') is None:
            raise Exception("Must provide an NCBI database to search using the ncbi-db setting.")

        params = {
                'db' : self.setting('ncbi-db'),
                'retMax' : self.setting('ret-max'),
                }

        params.update(provided_params)
        return params

    def work_data_filepath(self, i, start_date=None, batch_prefix=None):
        if batch_prefix is None:
            filename = self.setting('filepattern') % i
        else:
            filename = self.setting('filepattern') % ("%s%s" % (batch_prefix, i))

        if start_date is None:
            return os.path.join(self.work_dir(), filename)
        else:
            return os.path.join(self.period_work_dir(start_date), filename)

    def cache_data_filepath(self, i, start_date=None, batch_prefix=None):
        if batch_prefix is None:
            filename = self.setting('filepattern') % i
        else:
            filename = self.setting('filepattern') % ("%s%s" % (batch_prefix, i))

        if start_date is None:
            return os.path.join(self.cache_dir(), filename)
        else:
            return os.path.join(self.period_cache_dir(start_date), filename)

    def initial_search(self, search_term, start_date=None, end_date=None):
        """
        Method which implements the initial search.

        If start and end dates are provided, these are included in the search.

        Returns a count of records, a WebEnv value and a QueryKey value which
        can then be used to fetch the full results.
        """
        params = {
                'term' : search_term,
                'usehistory' : 'y',
                'retMax' : self.setting('initial-ret-max')
                }

        if start_date and end_date:
            params.update({
                'datetype' : self.setting('datetype'),
                'mindate' : start_date.strftime("%Y/%m/%d"),
                'maxdate' : (end_date - datetime.timedelta(days=1)).strftime("%Y/%m/%d") # TODO is this right?
                })
        elif start_date or end_date:
            raise Exception("Both start and end date must be provided if either is.")

        self.print_progress("  search params being used: %s" % params)
        result = requests.get(self.search_url(), params=self.search_params(params))

        root = ET.fromstring(result.text)
    
        error = root.find("ERROR")
        if error is not None:
            raise APIError(error.text)

        count = int(root.find("Count").text)
        web_env = root.find("WebEnv").text
        query_key = root.find("QueryKey").text
        
        db = self.setting('ncbi-db')
        self.print_progress("  found %s total articles in %s matching the search" % (count, db))

        return (count, web_env, query_key)

    def fetch_batch(self, i, retstart, retmax, web_env, query_key, start_date=None, batch_prefix=None):
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

        work_file = self.work_data_filepath(i, start_date, batch_prefix)
        self.print_progress("saving data to %s" % work_file)
        with open(work_file, "wb") as f:
            for block in result.iter_content(1024):
                if not block:
                    break
                f.write(block)

    def search_and_fetch(self, term, start_date = None, end_date = None):
        count, web_env, query_key = self.initial_search(term, start_date, end_date)

        i = 0
        retstart = 0
        retmax = self.setting('ret-max')

        while retstart < count:
            self.fetch_batch(i, retstart, retmax, web_env, query_key, start_date)
            retstart += retmax
            i += 1

    def parse_date(self, entry):
        if entry is not None:
            day_is_none = False
            month_is_none = False

            year = entry.findtext("Year")
            month = entry.findtext("Month")
            day = entry.findtext("Day")

            if day is None:
                day_is_none = True
                day = "1"

            if month is None:
                month_is_none = True
                month = "1"

            if year is not None:
                datestring = '%s %s %s' % (year, month, day)
                date = dateutil.parser.parse(datestring)

                if month_is_none:
                    return date.strftime("%Y")
                elif day_is_none:
                    return date.strftime("%Y-%m")
                else:
                    return date.strftime("%Y-%m-%d")

    def create_repository(self, name):
        args = {"name" : name, "source" : self.db_source(), "log" : self.db_source()}
        return Repository.update_or_create_by_name(args, "")

    def yield_soup(self, start_date=None):
        if start_date is None:
            cache_dir = self.cache_dir()
        else:
            cache_dir = self.period_cache_dir(start_date)

        for filename in os.listdir(cache_dir):
            filepath = os.path.join(cache_dir, filename)
            with open(filepath, 'rb') as f:
                soup = BeautifulSoup(f, "xml")
            yield soup

    # Parsing Methods (may be pubmed-specific)

    def doi(self, soup):
        doi = soup.find("ArticleId", IdType="doi")
        if doi is not None:
            return doi.getText()

    def article_ids(self, soup):
        for s in soup.ArticleIdList.find_all("ArticleId"):
            yield (s['IdType'], s.getText())

class UpdateByDOI(NCBI):
    """
    Search an NCBI database for information about all articles in the database by DOI.

    There's no `process` method implemented since we might want to do multiple
    things with the returned data, so subclass this for the particular parsing
    behavior you need.
    """
    aliases = ['ncbi-doi']

    _settings = {
            'max-items' : ("Maximum number of DOIs in a single API request.", 100),
            'filepattern' : 'data-%s.xml'
            }

    def scrape(self):
        articles_with_dois = Article.select().where(~(Article.doi >> None))

        max_items = self.setting('max-items')
        n_articles = articles_with_dois.count()
        n_batches = n_articles/max_items+1

        for batch in range(n_batches+1):
            articles = articles_with_dois.paginate(batch, max_items)
            dois = ["%s[AID]" % article.doi for article in articles]
            self.print_progress("    about to fetch batch %s of %s (%s articles)" % (batch+1, n_batches+1, len(dois)))
            term = " OR ".join(dois)

            count, web_env, query_key = self.initial_search(term)

            i = 0
            retstart = 0
            retmax = self.setting('ret-max')

            while retstart < count:
                self.fetch_batch(i, retstart, retmax, web_env, query_key, None, batch)
                retstart += retmax
                i += 1


class UpdateExternalIdsByDOI(UpdateByDOI):
    """
    Create instances based on external IDs reported by NCBI/pubmed.
    """
    aliases = ['pubmed-update-repositories']
    _settings = {
            'ncbi-db' : 'pubmed'
            }

    def process(self):
        for soup in self.yield_soup():
            for article_soup in soup.find_all("PubmedArticle"):
                doi = self.doi(article_soup)
                if doi is None:
                    continue
                article = Article.from_doi(doi)
                external_ids = self.article_ids(article_soup)

                for id_type, id_value in external_ids:
                    info = pubmed_external_ids[id_type]
                    if info is None:
                        continue

                    Instance.create(
                            article=article,
                            repository=self.create_repository(info['name']),
                            free_to_read=info['free_to_read'],
                            identifier=id_value,
                            source=self.db_source(),
                            log=self.db_source())

                    log_args = (id_value, info['name'], article.doi, self.db_source())
                    article.log = article.log + "\nAdded external id %s for %s based on DOI %s via %s" % log_args

                article.save()

class NCBIArticles(ArticleScraper, NCBI):
    """
    Base class for article scrapers querying NCBI databases (such as pubmed).
    """
    aliases = ['ncbiarticles']
    _settings = {
            "search" : ("Search query to include.", None),
            "journals" : ("Shortcut to search the provided list of journals. Combined with any additional query using AND.", None),
            'cache-expires' : None
            }

    def search_term(self):
        journals = self.setting('journals')
        raw_search = self.setting('search')

        if journals is not None:
            journal_search_term = "(" + " OR ".join("\"%s\"[Journal]" % journal for journal in journals) + ")"
            if raw_search is None:
                search = journal_search_term
            else:
                search = "%s AND %s" % (journal_search_term, raw_search)
        else:
            search = raw_search

        return search

    def scrape_period(self, start_date, end_date):
        self.search_and_fetch(self.search_term(), start_date, end_date)

class Pubmed(NCBIArticles):
    """
    Creates a single ArticleList and individual Article objects for all
    articles returned from pubmed matching the [required] search query.
    """
    aliases = ['pubmed']
    _settings = {
            "ncbi-db" : "pubmed"
            }

    def purge_period(self, start_date):
        Article.delete().where(
                (Article.period == start_date.strftime("%Y-%m")) &
                (Article.source == self.db_source())
                ).execute()

    def article_list_name(self, start_date):
        if self.setting('journals') is not None:
            journal_string = "within %s journals" % len(self.setting('journals'))
        args = (self.setting('search'), journal_string,  start_date.strftime("%Y-%m"),)
        return "pubmed search: '%s' %s %s" % args

    def is_period_stored(self, start_date):
        article_list_name = self.article_list_name(start_date)
        try:
            ArticleList.get(
                (ArticleList.name == article_list_name) &
                (ArticleList.source == self.db_source())
                )
            return True
        except ArticleList.DoesNotExist:
            return False

    def create_article_list(self, start_date):
        return ArticleList.create(
                name = self.article_list_name(start_date),
                source = self.db_source(),
                log = self.db_source())

    def process_period(self, start_date, end_date):
        nihm_repository = self.create_repository(nihm_name)
        pmc_repository = self.create_repository(pmc_name)
        pubmed_repository = self.create_repository(pubmed_name)
        cache_dir = self.period_cache_dir(start_date)

        # TODO convert this to BeautifulSoup instead of etree

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

                    journal = Journal.update_or_create_by_issn({
                        'issn' : issn,
                        'title' : journal_title,
                        'source' : self.db_source(),
                        'log' : self.db_source()
                        },
                        "Updated by %s using issn" % self.db_source()
                        )

                    # Parse article info
                    title = article_entry.findtext("ArticleTitle")

                    # Parse date info
                    date_published = None
                    journal_pubdate_entry = journal_entry.find("JournalIssue").find("PubDate")

                    if journal_pubdate_entry is not None:
                        date_published = self.parse_date(journal_pubdate_entry)
                    else:
                        print "  no journal pub date, skipping article", title
                        continue

                    doi_entry = article_entry.find("ELocationID")

                    doi = None
                    if doi_entry is not None:
                        eid_type = doi_entry.get("EIdType")
                        if eid_type == 'doi':
                            doi = doi_entry.text

                    pubmed_id = medline_citation.findtext("PMID")

                    nihm_id = None
                    pmc_id = None
                    for other_id in medline_citation.findall("OtherID"):
                        other_id_text = other_id.text
                        if other_id_text.startswith("NIHM"):
                            nihm_id = other_id_text
                        elif other_id_text.startswith("PMC"):
                            pmc_id = other_id_text
                        else:
                            pass

                    assert title is not None

                    article = Article.create(
                            title = title,
                            doi = doi,
                            journal = journal,
                            period = start_date.strftime("%Y-%m"),
                            date_published = date_published,
                            source = self.db_source(),
                            log = self.db_source())

                    if nihm_id is not None:
                        Instance.create(
                                article=article,
                                repository=nihm_repository,
                                identifier=nihm_id,
                                source=self.db_source(),
                                log=self.db_source())

                    if pmc_id is not None:
                        Instance.create(
                                article=article,
                                repository=pmc_repository,
                                identifier=pmc_id,
                                source=self.db_source(),
                                log=self.db_source())

                    if pubmed_id is not None:
                        Instance.create(
                                article=article,
                                repository=pubmed_repository,
                                identifier=pubmed_id,
                                source=self.db_source(),
                                log=self.db_source())
