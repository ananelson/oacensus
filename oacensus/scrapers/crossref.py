from oacensus.models import Article
from oacensus.models import JournalList
from oacensus.models import Publisher
from oacensus.scraper import ArticleInfoScraper
from oacensus.scraper import JournalScraper
from oacensus.utils import parse_crossref_coins
import csv
import json
import os
import requests
import urllib

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

        crossref_list = JournalList.create(name = "Crossref Journals")

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
                        'publisher' : Publisher.create_or_update_by_name(row['Publisher'])
                        }

                self.create_or_modify_journal(issn, args, crossref_list)

        return crossref_list

class Crossref(ArticleInfoScraper):
    """
    Gets crossref information for all articles with DOIs in the database.

    Currently this does nothing with the returned data.
    """
    aliases = ['crossref']

    _settings = {
            'base-url' : ("Base url of crossref API", "http://search.labs.crossref.org/dois")
            }

    def process(self):
        articles = Article.select().where(Article.doi)
        for article in articles:
            response = requests.get(self.setting('base-url'),
                    params = {'q' : article.doi}
                    )
            crossref_info = json.loads(response.text)

            if crossref_info:
                coins = parse_crossref_coins(crossref_info[0])
                journal_title = coins['rft.jtitle'][0]
                print "journal title", journal_title
