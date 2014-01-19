from oacensus.commands import defaults
from oacensus.scraper import Scraper
from datetime import date
import re
from nose.exc import SkipTest

TEST_PROJECT_ID = "7ABA7C67-FF06-4655-BBED-A0186A93C797"
TEST_GRANT_REF = "BBS/E/C/00005040"
TEST_ORG_ID = "B1F0E8FE-FE3C-49ED-9C96-1ED75312A8A0"
TEST_FUNDER = "AHRC"

gtr_id_regex = re.compile('([A-Z0-9]{8}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{12})')

def test_article_from_project_id():
    gtr = Scraper.create_instance('gtr', defaults)

    article_list = gtr.fetch_articles_for_project(TEST_PROJECT_ID)
    assert len(article_list) > 4

def test_grant_id_from_ref():
    gtr = Scraper.create_instance('gtr', defaults)
    id = gtr.get_project_id_from_grant_code(TEST_GRANT_REF)

    assert id == TEST_PROJECT_ID


def test_grant_id_from_org_id():
    gtr = Scraper.create_instance('gtr', defaults)
    gtr.update_settings({'testing' : True})
    ids = gtr.get_project_ids_from_org_id(TEST_ORG_ID)

    assert len(ids) > 20
    test_id = ids[0]
    assert gtr_id_regex.match(test_id) is not None

def test_projects_ids_from_funder():
    gtr = Scraper.create_instance('gtr', defaults)
    gtr.update_settings({'testing' : True})
    projects = gtr.get_project_ids_from_funder_name(TEST_FUNDER)

    assert len(projects) == 80
    test_id = projects[0]
    assert gtr_id_regex.search(test_id)

def test_scraper_funder():
    raise SkipTest()

    gtr = Scraper.create_instance('gtr', defaults)
    gtr.update_settings(
            {
             'testing' : True,
             'search-type' : 'council',
             'search' : 'AHRC'
             }
                        )
    article_list = gtr.run()
    assert len(article_list.articles()) > 90
    for article in article_list.articles():
        assert article.title
        assert isinstance(article.date_published, date)

def test_scraper_org():
    raise SkipTest()

    gtr = Scraper.create_instance('gtr', defaults)
    gtr.update_settings(
            {
             'testing' : True,
             'search-type' : 'organisation',
             'search' : TEST_ORG_ID
             }
                        )
    article_list = gtr.run()
    assert len(article_list.articles()) > 1000
    for article in article_list.articles():
        assert article.title
        assert isinstance(article.date_published, date)

def test_scraper_grantref():
    gtr = Scraper.create_instance('gtr', defaults)
    gtr.update_settings(
            {
             'testing' : True,
             'search-type' : 'project',
             'search' : TEST_GRANT_REF
             }
                        )
    article_list = gtr.run()
    assert len(article_list.articles()) == 5
    for article in article_list.articles():
        assert article.title
        assert isinstance(article.date_published, date)



