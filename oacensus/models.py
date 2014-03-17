from peewee import *

from oacensus.db import db

class ModelBase(Model):
    source = CharField(help_text="Which scraper populated this information?")

    def truncate_title(self, length=40):
        title = self.title
        if len(title) < length:
            if type(title) is str:
                return title.decode("utf-8", "ignore")
            else:
                return title
        else:
            truncated = title[0:length]
            if type(truncated) is str:
                truncated = truncated.decode("utf-8", "ignore")
            return u"{0}...".format(truncated)

    class Meta:
        database = db

    @classmethod
    def delete_all_from_source(klass, source):
        return klass.delete().where(klass.source == source).execute()

    @classmethod
    def count_from_source(klass, source):
        return klass.select().where(klass.source == source).count()

    def __unicode__(self):
        return u"TODO IMPLEMENT UNICODE FOR %s" % self.__class__.__name__

    def __str__(self):
        return unicode(self).encode("ascii", "ignore")

class License(ModelBase):
    alias = CharField()
    title = CharField()
    url = CharField()

    def __unicode__(self):
        return u"<License {0}: {1}>".format(self.alias, self.title)

    @classmethod
    def find_license(klass, alias):
        try:
            return License.get((License.alias == alias) | (License.url == alias) | (License.title == alias))
        except License.DoesNotExist:
            return LicenseAlias.get(LicenseAlias.alias == alias).license

class LicenseAlias(ModelBase):
    license = ForeignKeyField(License)
    alias = CharField(unique=True)

class Publisher(ModelBase):
    name = CharField()

    def __unicode__(self):
        return u"<Publisher {0}: {1}>".format(self.id, self.name)

    @classmethod
    def find_or_create_by_name(cls, name, source):
        try:
            publisher = cls.get(cls.name == name)
        except Publisher.DoesNotExist:
            publisher = Publisher.create(name=name, source=source)

        return publisher

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
        issn = args['issn']
        try:
            journal = cls.get(cls.issn == issn)
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

    def is_free_to_read(self, on_date=None):
        "Is true if there is one Rating on the journal which indicates free-to-read."
        if on_date is not None:
            raise Exception("date ranges not implemented yet")
        return any(rating.free_to_read for rating in self.ratings)

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
        help_text="Web page for article information. Not a download URL, does not imply anything.")

    def __unicode__(self):
        return u'{0}'.format(self.truncate_title())

    def instance_for(self, repository_name):
        instances = self.instances.join(Repository).where(Repository.name == repository_name)
        if instances.count() > 0:
            return instances[0]

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

    @classmethod
    def find_or_create_by_name(cls, name, source):
        try:
            repo = cls.get(cls.name == name)
        except Repository.DoesNotExist:
            repo = Repository.create(name=name, source=source)

        return repo

class OpenMetaCommon(ModelBase):
    "Common fields shared by Rating and Instance tables."
    free_to_read = BooleanField(null=True,
            help_text="Are journal contents available online for free?")
    license = ForeignKeyField(License, null=True)
    start_date = DateField(null=True,
            help_text="This rating's properties are in effect commencing from this date.")
    end_date = DateField(null=True,
            help_text="This rating's properties are in effect up to this date.")

    def validate_downloadable(self):
        """
        Validate that the article is available at the designated URL and
        corresponds to expected or min file size and expected file type, if
        provided.
        """
        raise Exception("not implemented")

class Rating(OpenMetaCommon):
    journal = ForeignKeyField(Journal, related_name="ratings")

    def __unicode__(self):
        return u"<Rating {1} on {0}>".format(self.journal.title, self.id)

class Instance(OpenMetaCommon):
    article = ForeignKeyField(Article, related_name="instances")
    repository = ForeignKeyField(Repository,
        help_text="Repository in which this instance is deposited or described.")
    identifier = CharField(null=True,
            help_text = "Identifier within the repository.")
    info_url = CharField(null=True,
            help_text = "For convenience, URL of an info page for the article.")
    download_url = CharField(null=True,
            help_text = "URL for directly downloading the article. May be tested for status and file size.")
    expected_file_size = CharField(null = True,
            help_text = "Expected file size if article is downloadable.")
    expected_file_hash = CharField(null = True,
            help_text = "Expected file checksum if article is downloadable.")

    def __unicode__(self):
        return u"<Instance '{0}' ({2}) in {1}>".format(self.article.truncate_title(), self.repository.name, self.identifier)

class JournalList(ModelBase):
    name = CharField()

    def __unicode__(self):
        args = (len(self.journals()), self.name, self.id)
        return u"<Journal List {2} ({0}): {1}>".format(*args)

    def __len__(self):
        return self.memberships.count()

    def __getitem__(self, key):
        return self.memberships[key].journal

    def add_journal(self, journal, source):
        JournalListMembership(
            journal_list = self,
            source = source,
            journal = journal
        ).save()

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
    LicenseAlias.create_table()
    Journal.create_table()
    JournalList.create_table()
    JournalListMembership.create_table()
    Publisher.create_table()
    Repository.create_table()

def delete_all(delete_licenses = False):
    Article.delete().execute()
    ArticleList.delete().execute()
    ArticleListMembership.delete().execute()
    Instance.delete().execute()
    Rating.delete().execute()
    Journal.delete().execute()
    JournalList.delete().execute()
    JournalListMembership.delete().execute()
    Publisher.delete().execute()
    Repository.delete().execute()

    if delete_licenses:
        License.delete().execute()
        LicenseAlias.delete().execute()

