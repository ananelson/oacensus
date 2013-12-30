from oacensus.exceptions import APIError
from oacensus.scraper import Scraper
import dateutil.parser
import os
import requests
import time
import json
import datetime
import re

DOI_REGEX = re.compile("\\b(10[.][0-9]{4,}(?:[.][0-9]+)*/(?:(?![\\/\"&\'<>])\\S)+)\\b")

class GTR(Scraper):
    """
    Base class for scrapers querying RCUK Gateway to Research
    """
    aliases = ['gtr', 'rcuk']
    _settings = {
            "base-url" : ("Base URL of API", "http://gtr.rcuk.ac.uk/gtr/api/"),
            "base-headers" : ("HTTP Accept settings", {'Accept' : 'application/vnd.rcuk.gtr.json-v1'}),
            "data-file" : ("Name of cache file for data", "gtr-pubs.json"),
            "delay" : ("Time in seconds between API requests.", 0.5),
            "search-type" : ("One of 'person', 'project', 'council', or 'organisation'.", None),
            "search" : ("Term to search for. Must be a name, project code, council abbreviation, or GTR organisation ID.", None),
            "testing" : ("Reduce number of live API calls for testing purposes", False)
            }

    def fetch_articles_for_project(self, gtr_project_id):
        """
        Obtain articles given a GTR Project ID
        """
        self.print_progress("waiting for delay period")
        time.sleep (self.setting('delay'))
        msg = "collecting articles for project %s" % (gtr_project_id)
        self.print_progress(msg)

        url = "%sprojects/%s/outcomes/publications" % (self.setting('base-url'),
                                                       gtr_project_id)

        result = requests.get(url, headers = self.setting('base-headers'))

        totalpages = result.json().get('totalPages')
        publications = []
        publications.extend(result.json().get('publication'))

        params = {}
        page = 2
        while page <= totalpages:
            params['p'] = page
            result = requests.get(
                    url,
                    params = params,
                    headers = self.setting('base-headers')
                            )
            publications.extend(result.json().get('publication'))

            if self.setting('testing') == True and page > 3:
                page = totalpages
            page+=1

        return publications

    def get_project_id_from_grant_code(self, grantreference):
        """
        Obtain the GTR ID for a project from the RCUK grant code.
        """
        self.print_progress("waiting for delay period")
        time.sleep (self.setting('delay'))
        msg = "collecting GTR ID for project %s" % (grantreference)
        self.print_progress(msg)

        params = {
                    'q' : '"%s"' % (grantreference),
                    'f' : 'pro.id'
                }

        url = "%sprojects?" % (self.setting('base-url'))
        result = requests.get(
                    url,
                    params = params,
                    headers = self.setting('base-headers')
                            )

        project = result.json().get('project')
        assert len(project) == 1 # Should only ever get one result
        return result.json().get('project')[0].get('id')

    def get_project_ids_from_funder_name(self, funder, test=False):
        """
        Obtain the GTR Project IDs for a specific funder.
        """
        self.print_progress("waiting for delay period")
        time.sleep (self.setting('delay'))
        msg = "collecting GTR IDs for %s" % (funder)
        self.print_progress(msg)

        assert funder in ['AHRC', 'NERC', 'ESRC', 'BBSRC', 'EPSRC', 'STFC', 'MRC']
        params = {
                    'q' : funder,
                    'f' : 'fu.org.n'
                }

        url = "%sfunds?" % (self.setting('base-url'))
        result = requests.get(
                    url,
                    params = params,
                    headers = self.setting('base-headers')
                            )

        totalpages = result.json().get('totalPages')
        projects = []
        for fund in result.json().get('fund'):
            for link in fund.get('links').get('link'):
                if link.get('rel') == 'FUNDED':
                    projects.append(self.gtr_url_to_id(link.get('href')))

        page = 2
        while page <= totalpages:
            params['p'] = page
            result = requests.get(
                    url,
                    params = params,
                    headers = self.setting('base-headers')
                            )
            for fund in result.json().get('fund'):
                for link in fund.get('links').get('link'):
                    if link.get('rel') == 'FUNDED':
                        projects.append(self.gtr_url_to_id(link.get('href')))
            if self.setting('testing') == True and page > 3:
                page = totalpages
            page+=1

        return projects


    def get_project_ids_from_org_id(self, org_id):
        """
        Obtain GTR Grant IDs for an organisation ID
        """

        self.print_progress("waiting for delay period")
        time.sleep (self.setting('delay'))
        msg = "collecting GTR grant IDs for %s" % (org_id)
        self.print_progress(msg)

        url = "%sorganisations/%s/projects" % (self.setting('base-url'),
                                                org_id)

        params={}
        result = requests.get(
                    url,
                    headers = self.setting('base-headers')
                            )
        totalpages = result.json().get('totalPages')
        projects = []
        for proj in result.json().get('project'):
            projects.append(proj.get('id'))

        page = 2
        while page <= totalpages:
            params['p'] = page
            result = requests.get(
                    url,
                    headers = self.setting('base-headers')
                            )
            for proj in result.json().get('project'):
                projects.append(proj.get('id'))

            if self.setting('testing') == True and page > 3:
                page = totalpages
            page+=1

        return projects

    def gtr_url_to_id(self, href):
        return href.split('/')[-1]

    def parse_timestamp(self, timedelta):
        delta = datetime.timedelta(0,0,0, int(timedelta))
        epoch = datetime.date(1970, 1,1)
        return epoch + delta

    def parse_href_doi(self, href):
        doi = DOI_REGEX.findall(href)[0]
        return doi

    def scrape(self):
        """
        Scrape method for various search types
        """

        current_request = self.setting('search-type')
        current_search_term = self.setting('search')
        if current_request == 'council':
            result = self.get_project_ids_from_funder_name(current_search_term)
            current_request = 'project_from_id'
            project_list = result

        if current_request == 'organisation':
            result = self.get_project_ids_from_org_id(current_search_term)
            current_request = 'project_from_id'
            project_list = result

        if current_request == 'project':
            project_id = self.get_project_id_from_grant_code(current_search_term)
            current_request = 'project_from_id'
            project_list = [project_id]

        if current_request == 'project_from_id':
            publications = []
            for project in project_list:
                publications.extend(self.fetch_articles_for_project(project))

        if current_request == 'person':
            raise NotImplementedError #TODO

        data_file = os.path.join(self.work_dir(), self.setting('data-file'))
        with open(data_file, 'wb') as f:
            json.dump(publications, f)

    def process(self):
        from oacensus.models import ArticleList
        from oacensus.models import Article
        from oacensus.models import Journal

        data_file = os.path.join(self.cache_dir(), self.setting('data-file'))
        with open(data_file, 'rb') as f:
            publications = json.load(f)

        article_list = ArticleList.create(
                name = "GtR query for %s:%s" % (
                                self.setting('search-type'),
                                self.setting('search')
                                                )
                                        )

        for pub in publications:
            journal_title = pub.get('journalTitle') if pub.get('journalTitle') is not 'null' else None

            if journal_title:

                href = pub.get('doi') if pub.get('doi') is not 'null' else None
                if href:
                    doi = self.parse_href_doi(href)
                else:
                    doi = None
                journal_title = pub.get('journalTitle') if pub.get('journalTitle') is not 'null' else None
                issn = pub.get('issn') if pub.get('issn') is not 'null' else None
                title = pub.get('title') if pub.get('title') is not 'null' else None
                timestamp = pub.get('datePublished') if pub.get('datePublished') is not 'null' else None
                if timestamp:
                    date_published = self.parse_timestamp(timestamp)
                else:
                    date_published = None

                journal = Journal.create_or_update_by_issn({
                            'issn' : issn,
                            'title' : journal_title,
                            'source' : self.alias
                            })


                assert title is not None

                article = Article.create(
                                title = title,
                                source = self.alias,
                                doi = doi,
                                journal = journal,
                                date_published = date_published
                                )

                article_list.add_article(article)

        print "  ", article_list
        return article_list


