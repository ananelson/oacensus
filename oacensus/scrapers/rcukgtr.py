from oacensus.scraper import Scraper
from oacensus.models import Article
from oacensus.models import ArticleList
from oacensus.models import Instance
from oacensus.models import Journal
from oacensus.models import Repository
import os
import requests
import time
import json
import codecs

search_types = ['person', 'project', 'grant', 'funder', 'organisation']

class GTR(Scraper):
    """
    Create articles from projects defined in RCUK Gateway to Research.

    Uses gtr2 API.
    """
    aliases = ['gtr', 'gtrarticles']
    _settings = {
            "base-url" : ("Base URL of API", "http://gtr.rcuk.ac.uk/gtr/api/"),
            "base-headers" : ("HTTP Accept settings", {'Accept' : 'application/vnd.rcuk.gtr.json-v1'}),
            "data-file" : ("Pattern to use to store data in cache.", "%s--%03d.json"),
            "funders" : ("List of possible funding organizations.", ['AHRC', 'NERC', 'ESRC', 'BBSRC', 'EPSRC', 'STFC', 'MRC']),
            "limit" : None,
            "pagination-keys" : ("Keys which give pagination information.",  [u'totalPages', u'totalSize', u'page', u'size']),
            "search-type" : ("One of %s" % (", ".join(search_types)), None),
            "search" : ("Term to search for.", None),
            "testing" : ("Reduce number of live API calls for testing purposes", False)
            }

    def make_request(self, path, params=None):
        url = "%s%s" % (self.setting('base-url'), path)
        self.print_progress("    making request to %s with params %s" % (url, params))
        return requests.get(url, params=params, headers=self.setting('base-headers'))

    def save_page(self, project_id, number, contents):
        filename = self.setting('data-file') % (project_id, number)
        filepath = os.path.join(self.work_dir(), filename)
        with codecs.open(filepath, 'w', encoding="UTF-8") as f:
            f.write(contents)

    def all_items_in_page(self, page):
        item_key = self.item_key_for_page(page)
        return page[item_key]

    def item_key_for_page(self, page):
        return [k for k in page.keys() if k not in self.setting('pagination-keys')][0]

    def fetch_page(self, page_num, total_pages, path, params):
        if params is None:
            params = {}

        self.print_progress("    fetching page %s of %s" % (page_num, total_pages))
        params['p'] = page_num
        response = self.make_request(path, params)
        return response.text

    def yield_all_items(self, path, params=None):
        """
        Handles pagination and fetches each page, yielding each item on each page.
        """
        response = self.make_request(path, params)
        page = json.loads(response.text)

        total_pages = page['totalPages']

        for item in self.all_items_in_page(page):
            yield item

        for page_num in range(2, total_pages):
            response_text = self.fetch_page(page_num, total_pages, path, params)
            page = json.loads(response_text)
            for item in self.all_items_in_page(page):
                yield item

    def save_all_pages(self, project_id, path, params=None):
        """
        Handles pagination and saves all pages with more than 0 elements.
        """
        response = self.make_request(path, params)
        page_text = response.text
        page = json.loads(page_text)

        total_pages = page['totalPages']

        if page['totalSize'] == 0:
            return

        self.save_page(project_id, 1, page_text)

        for page_num in range(2, total_pages):
            response_text = self.fetch_page(page_num, total_pages, path, params)
            self.save_page(project_id, page_num, response_text)

    def scrape_projects_for_funder(self, search_query):
        assert search_query in self.setting('funders')
        limit = self.setting('limit')
        path = "funds"
        params = { 'q' : search_query, 'f' : 'fu.org.n' }

        projects = []
        for i, fund in enumerate(self.yield_all_items(path, params)):
            if limit is not None and i > limit:
                print "Reached limit of", limit
                break
            funded = fund['links']['link'][1]
            assert funded['rel'] == "FUNDED"
            project_url = funded['href']
            assert len(project_url) == 78
            assert project_url[33:40] == 'project'
            project_id = project_url[42:78]
            projects.append(project_id)

        return projects

    def scrape_project_for_grant(self, search_query):
        path = "projects"
        params = {
                'q' : '"%s"' % search_query,
                'f' : 'pro.id'
                }

        response = self.make_request(path, params)
        page = json.loads(response.text)
        items = self.all_items_in_page(page)
        assert len(items) == 1
        return items[0]['id']

    def scrape(self):
        """
        Scrape method for various search types
        """
        search_type = self.setting('search-type')
        search_query = self.setting('search')

        assert search_type in search_types

        # Get list of projects based on search query.
        if search_type == 'project':
            projects = [search_query]

        elif search_type == 'organisation':
            path = "organisations/%s/projects" % search_query
            projects = [project.get('id') for project in self.yield_all_items(path)]

        elif search_type == 'funder':
            projects = self.scrape_projects_for_funder(search_query)

        elif search_type == 'grant':
            projects = [self.scrape_project_for_grant(search_query)]

        else:
            msg = "Unexpected search type '%s' was not caught by search types whitelist: %s"
            raise Exception(msg % (search_type, ", ".join(search_types)))

        # Search for articles.
        for project_id in projects:
            self.print_progress("    searching for publications from project %s" % project_id)
            path = "projects/%s/outcomes/publications" % project_id
            self.save_all_pages(project_id, path)

    def create_gtr_repository(self):
        return Repository.find_or_create_by_name({
            "name" : "RCUK Gateway to Research",
            "source" : self.db_source(),
            "log" : "Created by %s" % self.db_source()
            })

    def create_article_list(self):
        return ArticleList.create(
                name = "GTR %s query: %s" % (self.setting('search-type'), self.setting('search')),
                source = self.db_source(),
                log = "Created by %s" % self.db_source()
                )

    def process(self):
        gtr_repository = self.create_gtr_repository()
        article_list = self.create_article_list()

        cache_dir = self.cache_dir()
        for filename in os.listdir(cache_dir):
            filepath = os.path.join(cache_dir, filename)

            assert filename[36:38] == "--", "filename or uuid format has changed"
            project_id = filename[0:36]

            with codecs.open(filepath, 'r', encoding="UTF-8") as f:
                page_info = json.load(f)

            for pub in self.all_items_in_page(page_info):
                is_valid_type = pub.get('type', '') in ('Yes', 'Journal Article')
                has_journal_title = pub.get('journalTitle') is not None
                is_article = has_journal_title or is_valid_type

                if not is_article:
                    # print "Skipping", pub.keys()
                    continue

                if pub.get('issn') is not None:
                    journal = Journal.find_or_create_by_issn({
                        "issn" : pub['issn'],
                        "title" : pub['journalTitle'],
                        "source" : self.db_source(),
                        "log" : "Created by %s" % self.db_source(),
                        })

                elif pub.get('journalTitle') is not None:
                    journal = Journal.find_or_create_by_title({
                        "title" : pub['journalTitle'],
                        "source" : self.db_source(),
                        "log" : "Created by %s" % self.db_source(),
                        })

                else:
                    print "No journal found in %s" % pub

                if pub.get('datePublished') is not None:
                    dps = int(pub['datePublished']) / 1000
                    date_published = time.strftime("%Y-%m-%d", time.gmtime(dps))
                else:
                    date_published = None

                if pub.get('doi') is not None:
                    doi = pub['doi'].replace("http://dx.doi.org/", "")
                else:
                    doi = None

                article = Article.create(
                        title = pub['title'],
                        doi = doi,
                        journal = journal,
                        date_published = date_published,
                        period = project_id,
                        source = self.db_source(),
                        log = "Created by %s from project id %s" % (self.db_source(), project_id)
                        )

                article_list.add_article(article, self.db_source())

                Instance.create(
                        article=article,
                        identifier=pub['id'],
                        repository=gtr_repository,
                        source=self.db_source(),
                        log="Created by %s" % self.db_source()
                        )

                if pub.get('pubMedId'):
                    Instance.create_pmid(article, pub['pubMedId'], self.db_source())

        return article_list
