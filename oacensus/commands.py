from modargs import args
from oacensus.models import Article, Journal, Publisher, ArticleList, JournalList
from oacensus.scraper import Scraper
import oacensus.load_plugins
import os
import sys

DEFAULT_COMMAND = 'help'
MOD = sys.modules[__name__]
PROG = 'oacensus'


defaults = {
    'cachedir' : '.oacensus/cache/',
    'workdir' : '.oacensus/work/'
}

def run():
    args.parse_and_run_command(sys.argv[1:], MOD, default_command=DEFAULT_COMMAND)

def help_command(on=False):
    args.help_command(PROG, MOD, DEFAULT_COMMAND, on)

def process_command(
        cachedir=defaults['cachedir'], # Directory to store cached scraped data.
        workdir=defaults['workdir'], # Directory to store temp working directories.
        ):

    pubmed = Scraper.create_instance('pubmed', locals())
    settings = {
        'search-term' : "science[journal] AND breast cancer AND 2008[pdat]"
        }
    pubmed.update_settings(settings)
    pubmed.run()
