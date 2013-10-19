from peewee import *
from oacensus.constants import dbfile

db = SqliteDatabase(dbfile)

class ModelBase(Model):
    class Meta:
        database = db

class Article(ModelBase):
    title = CharField()
    pubmed_id = CharField()
    nihm_id = CharField(null=True)
    pmc_id = CharField(null=True)
    date_published = DateField(null=True)
    date_created = DateField(null=True)
    date_completed = DateField(null=True)
            
class Journal(ModelBase):
    title = CharField()
    iso_abbreviation = CharField()
    issn = CharField()
    country = CharField()
    medline_ta = CharField()
    nlm_unique_id = CharField()
    issn_linking = CharField()

class Publisher(ModelBase):
    name = CharField()

class ArticleList(ModelBase):
    name = CharField()

class JournalList(ModelBase):
    name = CharField()

Article.create_table()
Journal.create_table()
Publisher.create_table()
ArticleList.create_table()
JournalList.create_table()
