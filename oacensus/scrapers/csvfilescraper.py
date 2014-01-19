from oacensus.models import Article, Journal
from oacensus.models import ArticleList
from oacensus.scraper import Scraper
from oacensus.utils import parse_datestring_to_date
import os
import datetime
import csv

class CSVScraper(Scraper):
    """
    Loads a list of articles from a CSV files assuming standard headings

    The scraper uses the csv.DictReader class to load the file and requires at a
    minimum that the column headings include an article title. The other columns
    that will be tested for are 'doi', 'journal', 'issn', and variations on
    'date_published'
    """

    aliases = ['csvfile']

    _settings = {
            'base-url' : ("Base url of crossref API", "http://search.labs.crossref.org/dois"),
            "csv-file" : ("Path to file containing list of DOIs.", "articles.csv"),
            "column-mapping" : ("Mapping from OA Census Article and Journal attributes to column headings in CSV file",
                                {
                                    'title' : 'title',
                                    'doi' : 'doi',
                                    'date_published' : 'date_published',
                                    'journal.title' : 'journal',
                                    'journal.issn' : 'issn',
                                    'journal.eissn' : 'eissn'
                                 }
                                ),
            "list-name" : ("Custom list name.", "Custom CSV List"),
            "data-file" : ("Name of cache file to store articles.", "work.csv"),
            "source" : ("'source' attribute to use for articles.", "csvlist")
            }

    def scrape(self):
        """
        Load CSV file, id correct columns, and write normalised CSV file

        The scrape function will load the CSV file and attempt to identify the
        correct columns for populating the required attributes for both Article and
        Journal types. A CSV file is written out containing those outputs that
        for which this has been successful so the Scraper can read in its own
        outputs.
        """

        msg = "collecting articles from file %s" % self.setting('data-file')
        self.print_progress(msg)


        articles = []
        with open(self.setting('csv-file'), 'rU') as f:
            reader = csv.DictReader(f)

            for art in reader:
                articledict = {}
                for key,value in self.setting('column-mapping').iteritems():
                    try:
                        articledict[key] = art.get(value)
                    except TypeError:
                         articledict[key] = None

                if articledict.get('title'):
                    articledict['title'] = unicode(articledict['title'],
                                                    'CP1252').encode('utf-8')
                    if articledict.get('journal.title'):
                        articledict['journal.title'] = unicode(articledict['journal.title'],
                                                    'CP1252').encode('utf-8')
                        articles.append(articledict)

        data_file = os.path.join(self.work_dir(), self.setting('data-file'))
        msg = "writing %s articles to file %s" % (
                                            str(len(articles)),
                                            data_file
                                                )
        self.print_progress(msg)


        with open(data_file, 'wb') as f:
            writer = csv.DictWriter(f, self.setting('column-mapping').keys())
            writer.writeheader()
            writer.writerows(articles)


    def process(self):

        data_file = os.path.join(self.cache_dir(), self.setting('data-file'))
        with open(data_file, 'rU') as f:
            reader = csv.DictReader(f)

            article_list = ArticleList.create(name=self.setting('list-name'))
            for art in reader:
                if art.get('journal.issn'):
                    journal = Journal.create_or_update_by_issn(
                                {
                                 'title' : art.pop('journal.title'),
                                 'issn' : art.pop('journal.issn'),
                                 'eissn' : art.pop('journal.eissn', None),
                                 'source' : self.setting('source')
                                 }
                                )
                else:
                    journal = Journal.create(
                                title = art.pop('journal.title', 'No-journal-title'),
                                source = self.setting('source')
                                    )
                    art.pop('journal.issn', None),
                    art.pop('journal.eissn', None)

                art['date_published'] = parse_datestring_to_date(
                                                art.get('date_published')
                                                                )
                art['journal'] = journal
                art['source'] = self.setting('source')
                if art.get('doi'):
                    article = Article.create_or_update_by_doi(art)
                else:
                    article = Article.create(title = art.get('title'),
                                      source = self.setting('source')
                                      )

                article_list.add_article(article)

        print "  ", article_list
        return article_list






