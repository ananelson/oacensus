from oacensus.commands import defaults
from oacensus.scraper import Scraper
from tests.utils import setup_db

setup_db()

project_id = "7ABA7C67-FF06-4655-BBED-A0186A93C797"
grant_ref = "BBS/E/C/00005040"
org_id = "F9F1D136-12E3-4BE4-9668-0C9BC4A7C1BF"

def test_search_ftr_by_grant_id():
    scraper = Scraper.create_instance('gtr', defaults)
    settings = {'search_type' : 'grant', 'search' : grant_ref}
    scraper.update_settings(settings)
    article_list = scraper.run()
    assert len(article_list) > 5

def test_search_ftr_by_funder():
    scraper = Scraper.create_instance('gtr', defaults)
    settings = {'search_type' : 'funder', 'search' : 'AHRC', 'limit' : 50}
    scraper.update_settings(settings)
    article_list = scraper.run()
    assert len(article_list) > 40

def test_search_ftr_by_project():
    scraper = Scraper.create_instance('gtr', defaults)
    settings = {'search_type' : 'project', 'search' : project_id}
    scraper.update_settings(settings)
    article_list = scraper.run()
    assert len(article_list) > 4

def test_search_ftr_by_organisation():
    scraper = Scraper.create_instance('gtr', defaults)
    settings = {'search_type' : 'organisation', 'search' : org_id}
    scraper.update_settings(settings)
    article_list = scraper.run()
    assert len(article_list) > 500

