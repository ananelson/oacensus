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

    def __unicode__(self):
        return u"<Publisher {0}: {1}>".format(self.id, self.name)

    @classmethod
    def create_or_update_by_name(cls, name):
        try:
            publisher = cls.get(cls.name == name)
        except Publisher.DoesNotExist:
            publisher = Publisher.create(name = name)

        return publisher

class Journal(ModelBase):
    title = CharField(index=True,
        help_text="Name of journal.")
    url = CharField(null=True,
        help_text="Website of journal.")
    publisher = ForeignKeyField(Publisher, null=True,
        help_text="Publisher object corresponding to journal publisher.")
    source = CharField(
        help_text="Which scraper populated basic journal information?")
    issn = CharField(null=True, unique=True,
        help_text="ISSN of journal.")
    eissn = CharField(null=True,
        help_text="Electronic ISSN (EISSN) of journal.")
    doi = CharField(null=True, unique=True,
        help_text="DOI for journal.")

    open_access = BooleanField(null=True,
        help_text="Is this journal available as an open access journal?")
    open_access_source = CharField(null=True,
            help_text="Source of information (scraper alias) for open_access value.")
    license = CharField(null=True,
        help_text="Open source (or other) license on content.")

    subject = CharField(null=True,
        help_text="Subject area which this journal deals with.")
    country = CharField(null=True,
        help_text="Country of publication for this journal.")
    language = CharField(null=True,
        help_text="Language(s) in which journal is published.")
    start_year = IntegerField(null=True,
        help_text="Whatever DOAJ means by 'start year'.")

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
    title = CharField(
        help_text="Title of article.")
    doi = CharField(null=True,
        help_text="Digital object identifier for article.")
    date_published = DateField(null=True,
        help_text="Date on which article was published.")
    source = CharField()
    journal = ForeignKeyField(Journal, null=True,
        help_text="Journal object for journal in which article was published.")
    url = CharField(null=True,
        help_text="Web page for article information (and maybe content).")

    pubmed_id = CharField(null=True)
    nihm_id = CharField(null=True)
    pmc_id = CharField(null=True)

    free_to_read = BooleanField(null=True,
            help_text="Is article 'free to read' as per CrossRef?")
    open_access = BooleanField(null=True)
    open_access_source = CharField(null=True)
    license = CharField(null=True)

    def __unicode__(self):
        return u'{0}'.format(self.truncate_title())

    def is_open_access(self):
        if self.open_access is not None:
            return self.open_access
        elif self.journal is not None:
            return self.journal.open_access
        else:
            return None

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

    def __len__(self):
        return self.memberships.count()

    def __getitem__(self, key):
        return self.memberships[key].journal

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
        return u"<Article List ({0} articles): {1}>".format(*args)

    def __len__(self):
        return self.memberships.count()

    def __getitem__(self, key):
        return self.memberships[key].article

    def add_article(self, article):
        ArticleListMembership(
            article_list = self,
            article = article).save()

    def articles(self):
        return [membership.article for membership in self.memberships]

class ArticleListMembership(ModelBase):
    article_list = ForeignKeyField(ArticleList, related_name="memberships")
    article = ForeignKeyField(Article, related_name="memberships")

def create_db_tables():
    Article.create_table()
    ArticleList.create_table()
    ArticleListMembership.create_table()
    Journal.create_table()
    JournalList.create_table()
    JournalListMembership.create_table()
    Publisher.create_table()
