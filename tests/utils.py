from oacensus.db import db
from oacensus.models import create_db_tables
from oacensus.scraper import Scraper
import oacensus.load_plugins

def setup_db(create_licenses=True):
    "Sets up the database and initializes tables in memory, if not already initialized."
    db.init(':memory:')
    create_db_tables()
    if create_licenses:
        Scraper.create_instance('licenses').run()
