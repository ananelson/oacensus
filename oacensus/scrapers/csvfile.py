from oacensus.scrapers.tabularfile import TabularFile
import os
import csv
import codecs

class CSVFile(TabularFile):
    """
    Loads a list of articles from a CSV file.
    """

    aliases = ['csvarticles', 'csvfile']

    _settings = {
            "encoding" : 'utf-8'
            }

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
                article = self.create_article_for_info(info)
                article_list.add_article(article, self.db_source())

        self.print_progress(article_list)
        return article_list
