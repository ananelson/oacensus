from oacensus.scraper import Scraper

from tests.utils import setup_db
setup_db()

def test_scrape():
    list_name = "QUB APC Payments for RCUK 2013-14"
    source = "qub-2013-04"
    scraper = Scraper.create_instance('excelarticles')

    scraper.update_settings({
        "location" : "http://files.figshare.com/1464252/QUB_APC_payments_for_RCUK_2013_14.xlsx",
        "list-name" : list_name,
        "period" : "2013-14",
        "source" : source,
        "column-mapping" : {
            'Publisher' : 'publisher.name',
            'Article' : 'title',
            'DOI' : 'doi',
            }
        })

    article_list = scraper.run()
    assert len(article_list) == 26
