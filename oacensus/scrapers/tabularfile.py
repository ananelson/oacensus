import os
from oacensus.models import Publisher
from oacensus.models import Journal
from oacensus.models import Article
from oacensus.models import ArticleList
from oacensus.scraper import ArticleScraper
import shutil
import urllib

class TabularFile(ArticleScraper):
    """
    Base class for scrapers which parse tabular data files.
    """
    aliases = ['tabulararticles']

    _settings = {
            'location' : ("Path or URL for file containing article data.",  None),
            "data-file" : ("Name of cache file.", "work.txt"),
            "period" : ("Period to use, if no period is specified in a database row.", None),
            "list-name" : ("Custom list name.", None),
            "update-journal" : ("If true, update journal attributes. If false, only create new ones.", False),
            "column-mapping" : ("Mapping from Excel file headings to article and journal attributes.", None),
            }

    def scrape(self):
        location = self.setting('location')
        self.download_tabular_file(location)

    def download_tabular_file(self, location):
        work_file = os.path.join(self.work_dir(), self.setting('data-file'))
        if location is None:
            raise Exception("Must specify the path to file or URL of file")
        elif os.path.exists(location):
            shutil.copyfile(location, work_file)
        else:
            urllib.urlretrieve(location, work_file)

    def create_article_list(self):
        return ArticleList.create(
                name=self.setting('list-name'),
                source = self.db_source(),
                log = self.db_source())

    def create_article_for_info(self, info):
        """
        Given a dictionary of information, create the database objects.
        """
        info.pop(None)
        info['source'] = self.db_source()
        info['journal.source'] = self.db_source()
        info['publisher.source'] = self.db_source()
        info['log'] = self.db_source()
        info['journal.log'] = self.db_source()
        info['publisher.log'] = self.db_source()

        article_args = dict((k, v) for k, v in info.iteritems() if not "." in k)
        journal_args = dict((k.replace("journal.", ""), v) for k, v in info.iteritems() if k.startswith("journal."))
        publisher_args = dict((k.replace("publisher.", ""), v) for k, v in info.iteritems() if k.startswith("publisher."))

        if publisher_args.has_key('name'):
            publisher = Publisher.find_or_create_by_name(publisher_args)
        else:
            publisher = None

        journal_args['publisher'] = publisher

        if journal_args.has_key('issn'):
            if self.setting('update-journal'):
                journal = Journal.find_or_create_by_issn(journal_args)
            else:
                journal = Journal.update_or_create_by_issn(journal_args)
        elif journal_args.has_key('title'):
            if self.setting('update-journal'):
                journal = Journal.find_or_create_by_title(journal_args)
            else:
                journal = Journal.update_or_create_by_title(journal_args)
        else:
            journal = None

        if not article_args.has_key('period'):
            article_args['period'] = self.setting('period')

        return Article.create(journal=journal, **article_args)
