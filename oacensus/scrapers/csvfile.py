from oacensus.scrapers.tabularfile import TabularFile
import os
import csv
import codecs
from datetime import datetime
import re

class CSVFile(TabularFile):
    """
    Loads a list of articles from a CSV file.
    """

    aliases = ['csvarticles', 'csvfile']

    _settings = {
            "date-formats" : ( "Dictionary of regular expressions -> date formats.", {
                    "^[0-9]{4}$" : "%Y",
                    "^[0-9]{4}-[0-9]{2}$" : "%Y-%m",
                    "^[0-9]{2}/[0-9]{2}/[0-9]{4}$" : "%d/%M/%Y"
                    }),
            "encoding" : 'utf-8'
            }

    def parse_date_published(self, raw_date):
        date_published = None
        for regexp, date_format in self.setting('date-formats').iteritems():
            match = re.match(regexp, raw_date)
            if match:
                date_published = datetime.strptime(raw_date, date_format)
                break

        if date_published is None:
            raise Exception("No date format for %s" % raw_date)

        return date_published

    def process(self):
        data_file = os.path.join(self.cache_dir(), self.setting('data-file'))
        col_map = self.setting('column-mapping')

        article_list = self.create_article_list()

        with codecs.open(data_file, 'rU', encoding=self.setting('encoding')) as f:
            reader = csv.reader(f)

            headers = reader.next()
            col_map = self.setting('column-mapping')
            attributes = [col_map.get(h) for h in headers]

            for row in reader:
                if len(row) == 0:
                    break # assume we have reached end

                info = dict(zip(attributes, row))
                raw_date = info.pop('date_published')
                info['date_published'] = self.parse_date_published(raw_date)

                article = self.create_article_for_info(info)
                article_list.add_article(article, self.db_source())

        self.print_progress(article_list)
        return article_list
