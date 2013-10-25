from peewee import *
import sqlite3

from oacensus.db import db

class ModelBase(Model):
    def truncate_title(self, length=40):
        if len(self.title) < length:
            return self.title
        else:
            return self.title[0:length] + "..."

    class Meta:
        database = db

class Publisher(ModelBase):
    name = CharField()

class Journal(ModelBase):
    title = CharField()
    url = CharField(null=True)
    publisher = ForeignKeyField(Publisher, null=True)
    source = CharField() # where journal data was obtained from
    issn = CharField(null=True)
    eissn = CharField(null=True)

    open_access = BooleanField(null=True)
    open_access_source = CharField(null=True)
    license = CharField(null=True)

    subject = CharField(null=True)
    country = CharField(null=True)
    language = CharField(null=True)
    start_year = IntegerField(null=True)

    iso_abbreviation = CharField(null=True)
    medline_ta = CharField(null=True)
    nlm_unique_id = CharField(null=True)
    issn_linking = CharField(null=True)

    def __unicode__(self):
        return u"<Journal {0} [{1}]: {2}>".format(self.id, self.issn, self.truncate_title())

    def __str__(self):
        return unicode(self).encode('ascii', 'replace')

    @classmethod
    def create_or_update_by_issn(cls, args):
        try:
            journal = cls.get(cls.issn == args['issn'])
            for k, v in args.iteritems():
                if k != 'source':
                    setattr(journal, k, v)
            journal.save()
        except Journal.DoesNotExist:
            journal = Journal.create(**args)

        return journal

    @classmethod
    def by_issn(cls, issn):
        try:
            return cls.get(cls.issn == issn)
        except Journal.DoesNotExist:
            pass

class Article(ModelBase):
    title = CharField()
    doi = CharField(null=True)
    date_published = DateField(null=True)
    source = CharField()
    journal = ForeignKeyField(Journal, null=True)
    url = CharField(null=True)

    pubmed_id = CharField(null=True)
    nihm_id = CharField(null=True)
    pmc_id = CharField(null=True)

    free_to_read = BooleanField(null=True)
    open_access = BooleanField(null=True)
    open_access_source = CharField(null=True)
    license = CharField(null=True)

    def __unicode__(self):
        return u'{0}'.format(self.truncate_title())

    @classmethod
    def create_or_update_by_doi(cls, args):
        try:
            article = cls.get(cls.doi == args['doi'])
            for k, v in args.iteritems():
                setattr(article, k, v)
            article.save()
        except Article.DoesNotExist:
            article = Article.create(**args)

        return article

class JournalList(ModelBase):
    name = CharField()

    def __unicode__(self):
        args = (len(self.journals()), self.name)
        return u"<Journal List {0}: {1}>".format(*args)

    def add_journal(self, journal):
        JournalListMembership(
            journal_list = self,
            journal = journal).save()

    def journals(self):
        return [membership.journal for membership in self.memberships]

class JournalListMembership(ModelBase):
    journal_list = ForeignKeyField(JournalList, related_name="memberships")
    journal = ForeignKeyField(Journal, related_name="memberships")

class ArticleList(ModelBase):
    name = CharField()
    orcid = CharField(null=True)

    def __unicode__(self):
        args = (len(self.articles()), self.name)
        return u"<Article List {0}: {1}>".format(*args)

    def add_article(self, article):
        ArticleListMembership(
            article_list = self,
            article = article).save()

    def articles(self):
        return [membership.article for membership in self.memberships]

class ArticleListMembership(ModelBase):
    article_list = ForeignKeyField(ArticleList, related_name="memberships")
    article = ForeignKeyField(Article, related_name="memberships")

try:
    Article.create_table()
    ArticleList.create_table()
    ArticleListMembership.create_table()
    Journal.create_table()
    JournalList.create_table()
    JournalListMembership.create_table()
    Publisher.create_table()
except sqlite3.OperationalError:
    pass
