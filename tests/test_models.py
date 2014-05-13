from oacensus.models import Article
from oacensus.models import Instance
from oacensus.models import Journal
from oacensus.models import JournalList
from oacensus.models import JournalListMembership
from oacensus.models import License
from oacensus.models import Rating
from oacensus.models import Repository
from tests.utils import setup_db

setup_db()

def make_repo():
    return Repository.create_or_update_by_name({"name":"Test Repo", "source":"manual"})

def create_journal_and_article():
    "Create a journal and an article which is published in the journal."
    journal = Journal.create(title="The Journal", source="manual")
    article = Article.create(title="The Article", source="manual", period="2014-02", journal=journal)
    return (journal, article)

def test_open_meta_common():
    journal, article = create_journal_and_article()
    rating = Rating.create(journal=journal, free_to_read=True, source="manual")
    repository = make_repo()
    instance = Instance.create(article=article, repository=repository, free_to_read=True, source="manual")
    assert article.instances[0] == instance
    assert rating.free_to_read
    assert instance.free_to_read

def test_article_not_free_to_read():
    journal, article = create_journal_and_article()
    rating = Rating.create(journal=journal, free_to_read=False, source="manual")
    assert not article.journal.is_free_to_read()
    assert not article.is_free_to_read()

def test_article_free_to_read_from_journal():
    journal, article = create_journal_and_article()
    rating = Rating.create(journal=journal, free_to_read=True, source="manual")
    assert article.journal.is_free_to_read()
    assert article.is_free_to_read()

def test_article_free_to_read_from_repository():
    _, article = create_journal_and_article()
    repository = make_repo()
    instance = Instance.create(article=article, repository=repository,
            free_to_read=True, source="manual")
    assert instance in article.instances
    assert not article.journal.is_free_to_read()
    assert article.is_free_to_read()

def test_article_licenses():
    journal, article = create_journal_and_article()
    repository = make_repo()

    cc_by_license = License.find_license("cc-by")
    cc_nc_license = License.find_license("cc-by-nc")

    rating = Rating.create(journal=journal, license=cc_by_license, source="manual")
    assert article.licenses() == [cc_by_license]

    instance = Instance.create(article=article, repository=repository,
            license=cc_nc_license, source="manual")
    assert article.licenses() == [cc_by_license, cc_nc_license]

    assert article.has_license()
    assert article.has_open_license()
    assert article.has_open_license([cc_by_license])

def test_find_or_create():
    journal = Journal.create_or_update_by_issn({"issn" : "abc", "title" : "The Journal", "source" : "test"})
    assert journal.title == "The Journal"
    journal = Journal.create_or_update_by_issn({"issn" : "abc", "title" : "The Updated Journal"})
    assert journal.title == "The Updated Journal"

def test_article():
    pmid = "ABC1234"

    article = Article()
    article.title = "This Is A Title"
    article.period = "2014-02"
    article.source = "test"
    article.pubmed_id = pmid
    article.save()

def test_linking_journal_to_article():
    journal = Journal()
    journal.title = "My Journal"
    journal.source = "test"
    journal.save()

    article = Article()
    article.journal = journal
    article.period = "2014-02"
    article.source = "test"
    article.title = "My Article"
    article.save()

    assert article.journal.title == "My Journal"

def test_journal_list():
    journal_list = JournalList()
    journal_list.name = "Open Access Journals"
    journal_list.source = "test"
    journal_list.save()

    journal = Journal()
    journal.title = "An Open Access Journal"
    journal.source = "test"
    journal.save()

    membership = JournalListMembership()
    membership.journal_list = journal_list
    membership.journal = journal
    membership.source = 'test'
    membership.save()

    assert journal_list.journals()[0] == journal

def test_add_journal_to_list():
    journal_list = JournalList()
    journal_list.name = "Open Access Journals"
    journal_list.source = "test"
    journal_list.save()

    journal = Journal()
    journal.title = "An Open Access Journal"
    journal.source = "test"
    journal.save()

    journal_list.add_journal(journal, "test")
    assert journal_list.journals()[0] == journal
