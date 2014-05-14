from oacensus.models import Article
from oacensus.models import ArticleList
from oacensus.models import JournalList
from oacensus.models import Publisher
from oacensus.scraper import JournalScraper
from oacensus.scraper import Scraper
from oacensus.utils import parse_crossref_coins
import csv
import json
import os
import requests
import urllib
import hashlib
import codecs

class CrossrefArticles(Scraper):
    """
    Uses crossref API to look up article metadata based on DOI.

    Currently this method updates the canonical journal title and the
    publication date for each article.
    """
    aliases = ['crossref']

    _settings = {
            'base-url' : ("Base url of crossref API", "http://search.labs.crossref.org/dois")
            }

    def article_filename(self, article):
        return hashlib.md5(article.doi).hexdigest()

    def scrape(self):
        url = self.setting('base-url')
        articles = Article.select().where(~(Article.doi >> None))
        for article in articles:
            self.print_progress("Requesting info from crossref for %s" % article)
            response = requests.get(url, params = {'q' : article.doi})
            fp = os.path.join(self.work_dir(), self.article_filename(article))
            with codecs.open(fp, 'w', encoding="utf-8") as f:
                f.write(response.text)

    def process(self):
        articles = Article.select().where(~(Article.doi >> None))
        for article in articles:
            fp = os.path.join(self.cache_dir(), self.article_filename(article))
            with codecs.open(fp, 'r', encoding="utf-8") as f:
                raw_data = f.read()
            crossref_info = json.loads(raw_data)

            if crossref_info:
                coins = parse_crossref_coins(crossref_info[0])

                if "rft.jtitle" in coins:
                    journal_title = coins['rft.jtitle'][0]
                    if journal_title != article.journal.title:
                        logmsg = "\nChanged journal title from '%s' to '%s' using %s."
                        article.journal.log += logmsg % (article.journal.title, journal_title, self.db_source())
                        article.journal.title = journal_title
                        article.journal.save()

                if "rft.date" in coins:
                    date_published = coins['rft.date'][0]
                    article.date_published = date_published
                    article.log += "\nAdded date_published %s using %s." % (date_published, self.db_source())
                    article.save()

        # We don't create any new records
        self.create_dummy_db_entry()


class CrossrefJournals(JournalScraper):
    """
    Gets crossref information about all available journal titles.
    """
    aliases = ['crossrefjournals']

    _settings = {
            'add-new-journals' : True,
            'csv-url' : ("URL to download CSV file.", "http://www.crossref.org/titlelist/titleFile.csv"),
            'encoding' : 'utf-8',
            'data-file' : ("File to save data under.", "crossref.csv")
            }

    def scrape(self):
        url = self.setting('csv-url')
        data_file = os.path.join(self.work_dir(), self.setting('data-file'))
        urllib.urlretrieve(url, data_file)

    def process(self):
        crossref_data = os.path.join(self.cache_dir(), self.setting('data-file'))
        limit = self.setting('limit')

        crossref_list = JournalList.create(name = "Crossref Journals", source = self.alias)
        print "cross ref list", crossref_list

        with open(crossref_data, 'rb') as f:
            crossref_reader = csv.DictReader(f)

            for i, row in enumerate(crossref_reader):
                if limit is not None and i >= limit:
                    break

                raw_issn = row['issn|issn2']
                if "|" in raw_issn:
                    issn, issn2 = raw_issn.split("|")
                else:
                    issn = raw_issn

                if not "-" in issn:
                    issn = "%s-%s" % (issn[0:4], issn[4:8])

                def clean_title(text):
                    return text.replace("\\", "").replace("\"", "")

                args = {
                        'title' : clean_title(row['JournalTitle']),
                        'doi' : row['doi'],
                        'publisher' : Publisher.find_or_create_by_name(row['Publisher'], self.alias)
                        }

                self.create_or_modify_journal(issn, args, crossref_list)

        return crossref_list
