from oacensus.db import db
from oacensus.models import License
from oacensus.models import create_db_tables
from oacensus.scraper import Scraper
import sqlite3
import peewee
import oacensus.load_plugins

def setup_db(create_licenses=True):
    "Sets up the database and initializes tables in memory, if not already initialized."
    try:
        db.init(':memory:')
        create_db_tables()
    except peewee.OperationalError, sqlite3.OperationalError:
        pass

    if create_licenses and License.select().count() == 0:
        Scraper.create_instance('licenses').run()
