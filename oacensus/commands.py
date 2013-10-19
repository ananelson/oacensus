from modargs import args
from oacensus.scraper import Scraper
import sys

default_command = 'help'
mod = sys.modules[__name__]
prog = 'oacensus'

defaults = {
    'cachedir' : '.oacensus/cache/',
    'workdir' : '.oacensus/work/'
}

import oacensus.load_plugins

def run():
    """
    Calls python modargs.
    """
    args.parse_and_run_command(sys.argv[1:], mod, default_command=default_command)

def help_command(on=False):
    args.help_command(prog, mod, default_command, on)

def run_command(
        scrapers = ['elsevier', 'biomed', 'bc'], # list of scrapers to run in order
        cachedir=defaults['cachedir'], # Directory to store cached scraped data.
        workdir=defaults['workdir'], # Directory to store temp working directories.
        ):

    scrapers = ['elsevier']
    for alias in scrapers:
        pubmed = Scraper.create_instance(alias, locals())
        pubmed.run()
