from oacensus.models import Article
from oacensus.models import Journal
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

modes = ["none", "ifempty", "overwrite"]
modess = ", ".join(modes)

class CrossrefArticles(Scraper):
    """
    Uses crossref API to look up article metadata based on DOI.

    This method standardizes the journal title if available, and provides a
    publication date for each article. This is the limit of the data available
    at present.
    """
    aliases = ['crossref']

    _settings = {
            'base-url' : ("Base url of crossref API", "http://search.labs.crossref.org/dois"),
            "pub-date-mode" : ("Mode for applying publication date data, one of %s" % modess, "ifempty")
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
        pub_date_mode = self.setting('pub-date-mode')
        assert pub_date_mode in modes

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
                        logmsg = "\nChanged journal title from '%s' to '%s' (%s)."
                        article.journal.log += logmsg % (article.journal.title, journal_title, self.db_source())
                        article.journal.title = journal_title
                        article.journal.save()

                if "rft.date" in coins:
                    date_published = coins['rft.date'][0]

                    if pub_date_mode == "none":
                        pass
                    elif pub_date_mode == "ifempty":
                        if article.date_published is None:
                            article.date_published = date_published
                            article.log += "\nAdded date_published %s (%s)." % (date_published, self.db_source())
                        else:
                            article.log += "\nNot overwriting existing date_published with %s value %s" % (self.db_source(), date_published)

                    elif pub_date_mode == "overwrite":
                        article.date_published = date_published
                        article.log += "\nUpdated date_published %s (%s)." % (date_published, self.db_source())

                    article.save()

        self.create_dummy_db_entry()


class CrossrefJournals(JournalScraper):
    """
    Gets crossref information about all available journal titles.
    """
    aliases = ['crossrefjournals']

    _settings = {
            # http://ftp.crossref.org/titlelist/titleFile.csv
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

        crossref_list = self.create_journal_list()

        with open(crossref_data, 'rb') as f:
            crossref_reader = csv.DictReader(f)

            for i, row in enumerate(crossref_reader):
                if limit is not None and i >= limit:
                    break
                if i % 500 == 0:
                    self.print_progress("    parsing crossref journal csv row %s" % (i+1))

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
                        'issn' : issn,
                        'title' : clean_title(row['JournalTitle']),
                        'doi' : row['doi'],
                        'publisher' : self.create_publisher(row['Publisher']),
                        'source' : self.db_source(),
                        'log' : self.db_source()
                        }

                update_fields = set(args.keys()).difference(Journal.update_skip_fields())
                update_args = (", ".join(update_fields), self.db_source())

                try:
                    Journal.get(Journal.issn == issn)
                    update_msg = "\nUpdating fields %s by matched issn via %s." % update_args
                    journal = Journal.update_or_create_by_issn(args, update_msg)
                except Journal.DoesNotExist:
                    update_msg = "\nUpdating fields %s by matched name via %s." % update_args
                    journal = Journal.update_or_create_by_title(args, update_msg)

                crossref_list.add_journal(journal, self.db_source())

        return crossref_list
