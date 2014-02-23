from peewee import *
import sqlite3
import json

from oacensus.db import db

# TODO make sure this is included in install...
with open("oacensus/license-urls.json", 'rb') as f:
    license_urls = json.load(f)
with open("oacensus/license-aliases.json", 'rb') as f:
    license_aliases = json.load(f)

class ModelBase(Model):
    source = CharField(help_text="Which scraper populated this information?")

    def truncate_title(self, length=40):
        if len(self.title) < length:
            return self.title
        else:
            return self.title[0:length] + "..."

    class Meta:
        database = db

    def __str__(self):
        return unicode(self).encode('ascii', 'replace')

class Publisher(ModelBase):
    name = CharField()

    def __unicode__(self):
        return u"<Publisher {0}: {1}>".format(self.id, self.name)

    @classmethod
    def create_or_update_by_name(cls, name, source):
        try:
            publisher = cls.get(cls.name == name)
        except Publisher.DoesNotExist:
            publisher = Publisher.create(name=name, source=source)

        return publisher

class License(ModelBase):
    alias = CharField() # id
    title = CharField()
    url = CharField()

    domain_content = BooleanField()
    domain_data = BooleanField()
    domain_software = BooleanField()

    family = CharField()

    is_okd_compliant = BooleanField(
            help_text="Is the license open according to the Open Knowledge Definition? http://www.opendefinition.org/od/")
    is_osi_compliant = BooleanField(
            help_text="Is the license open according to the Open Source Definition? http://opensource.org/osd")

    maintainer = CharField()
    status = CharField()

    def __unicode__(self):
        return u"<License {0}: {1}>".format(self.alias, self.title)

    @classmethod
    def find_license_by_url(klass, url):
        """
        Returns the license instance corresponding to a license URL, using a
        local manually managed list of URLs to handle exceptions.
        """
        try:
            License.get(License.url == url)
        except License.DoesNotExist:
            license_alias = license_urls[url]
            return License.get(License.alias == license_alias)

    @classmethod
    def find_license_by_alias(klass, alias):
        """
        Returns the license instance corresponding to a license URL, using a
        local manually managed list of URLs to handle exceptions.
        """
        try:
            License.get(License.alias == alias)
        except License.DoesNotExist:
            custom_license_alias = license_aliases[alias]
            return License.get(License.alias == custom_license_alias)

class Journal(ModelBase):
    title = CharField(index=True,
        help_text="Name of journal.")
    url = CharField(null=True,
        help_text="Website of journal.")
    publisher = ForeignKeyField(Publisher, null=True,
        help_text="Publisher object corresponding to journal publisher.")
    issn = CharField(null=True, unique=True,
        help_text="ISSN of journal.")
    eissn = CharField(null=True,
        help_text="Electronic ISSN (EISSN) of journal.")
    doi = CharField(null=True,
        help_text="DOI for journal.")

    subject = CharField(null=True,
        help_text="Subject area which this journal deals with.")
    country = CharField(null=True,
        help_text="Country of publication for this journal.")
    language = CharField(null=True,
        help_text="Language(s) in which journal is published.")

    iso_abbreviation = CharField(null=True)
    medline_ta = CharField(null=True)
    nlm_unique_id = CharField(null=True)
    issn_linking = CharField(null=True)

    def __unicode__(self):
        return u"<Journal {0} [{1}]: {2}>".format(self.id, self.issn, self.truncate_title())

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

    period = CharField(
        help_text="Name of date-based period in which this article was scraped.")

    journal = ForeignKeyField(Journal, null=True,
        help_text="Journal object for journal in which article was published.")
    url = CharField(null=True,
        help_text="Web page for article information (and maybe content).")

    pubmed_id = CharField(null=True)
    nihm_id = CharField(null=True)
    pmc_id = CharField(null=True)

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

class Repository(ModelBase):
    name = CharField(null=True,
            help_text = "Descriptive name for the repository.")
    info_url = CharField(null=True,
            help_text = "For convenience, URL of info page for the repository.")

class OpenMetaCommon(ModelBase):
    "Common fields shared by Rating and Instance tables."
    free_to_read = BooleanField(null=True,
            help_text="Are journal contents available online for free?")
    license = ForeignKeyField(License, null=True)
    start_date = DateField(null=True,
            help_text="This rating's properties are in effect commencing from this date.")
    end_date = DateField(null=True,
            help_text="This rating's properties are in effect up to this date.")
    info_url = CharField(null=True,
            help_text = "For convenience, URL of an info page for the article.")
    download_url = CharField(null=True,
            help_text = "URL for directly downloading the article. May be tested for status and file size.")
    expected_file_size = CharField(null = True,
            help_text = "Expected file size if article is downloadable.")
    # min_file_size
    # expected_file_type

    def validate_downloadable(self):
        """
        Validate that the article is available at the designated URL and
        corresponds to expected or min file size and expected file type, if
        provided.
        """
        raise Exception("not implemented")

class Rating(OpenMetaCommon):
    journal = ForeignKeyField(Journal, related_name="ratings")

class Instance(OpenMetaCommon):
    article = ForeignKeyField(Article, related_name="instances")
    repository = ForeignKeyField(Repository, null=True,
        help_text="Repository in which this instance is deposited or described.")

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
            source = 'unknown',
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
            source = 'unknown',
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
    Instance.create_table()
    Rating.create_table()
    License.create_table()
    Journal.create_table()
    JournalList.create_table()
    JournalListMembership.create_table()
    Publisher.create_table()
    Repository.create_table()
