from oacensus.models import Article
from oacensus.models import Journal
from oacensus.models import ArticleList
from oacensus.scraper import ArticleScraper
import os
import csv
import shutil
import codecs
from datetime import datetime
import re

class CSVFile(ArticleScraper):
    """
    Loads a list of articles from a CSV file.

    The column-mapping attribute must list all CSV file column names that
    should be mapped to article or journal attributes. Unlisted columns will be
    ignored. Columns which correspond to journal attributes should be preceded
    by "journal.", otherwise they will be assumed to be article attributes.

    The minimum required fields are listed in the default column-mapping setting.
    """

    aliases = ['csvfile']

    _settings = {
            "csv-file" : ("Path to file containing article data.", "articles.csv"),
            "date-formats" : ( "Dictionary of regular expressions -> date formats.", {
                    "^[0-9]{4}$" : "%Y",
                    "^[0-9]{4}-[0-9]{2}$" : "%Y-%m",
                    "^[0-9]{2}/[0-9]{2}/[0-9]{4}$" : "%d/%M/%Y"
                    }),
            "data-file" : ("Name of cache file to store articles.", "work.csv"),
            "encoding" : 'utf-8',
            "column-mapping" : ("Mapping from CSV file headings to article and journal attributes.",
                                {
                                    'title' : 'title',
                                    'doi' : 'doi',
                                    'date_published' : 'date_published',
                                    'journal' : 'journal.title',
                                    'issn' : 'journal.issn',
                                 }
                                ),
            "list-name" : ("Custom list name.", "Custom CSV List"),
            "source" : ("'source' attribute to use for articles.", "csvlist")
            }

    def scrape(self):
        work_file = os.path.join(self.work_dir(), self.setting('data-file'))
        shutil.copyfile(self.setting('csv-file'), work_file)

    def process(self):
        data_file = os.path.join(self.cache_dir(), self.setting('data-file'))
        col_map = self.setting('column-mapping')
        article_list = ArticleList.create(name = self.setting('list-name'))

        with codecs.open(data_file, 'rU', encoding=self.setting('encoding')) as f:
            reader = csv.reader(f)

            headers = reader.next()
            col_map = self.setting('column-mapping')
            attributes = [col_map.get(h) for h in headers]

            for row in reader:
                if len(row) == 0:
                    break # assume we have reached end

                info = dict(zip(attributes, row))

                info.pop(None)

                issn = info.pop('journal.issn')
                journal_title = info.pop('journal.title')

                title = info.pop('title')
                doi = info.pop('doi')
                raw_date = info.pop('date_published')

                if len(info) > 0:
                    # TODO implement support for arbitrary additional article or journal attributes
                    raise Exception("Items left in info dict %s" % info)

                journal = Journal.create_or_update_by_issn({
                    'issn' : issn,
                    'title' : journal_title,
                    'source' : self.alias
                    })

                date_published = None
                for regexp, date_format in self.setting('date-formats').iteritems():
                    match = re.match(regexp, raw_date)
                    if match:
                        date_published = datetime.strptime(raw_date, date_format)

                if date_published is None:
                    raise Exception("No date format for %s" % raw_date)

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
