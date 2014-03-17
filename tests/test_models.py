from oacensus.models import Article
from oacensus.models import Repository
from oacensus.models import Rating
from oacensus.models import Instance
from oacensus.models import Journal
from oacensus.models import JournalList
from oacensus.models import JournalListMembership
from tests.utils import setup_db

setup_db()

def create_journal_and_article():
    journal = Journal.create(title="The Journal", source="manual")
    article = Article.create(title="The Article", source="manual", period="2014-02")
    return (journal, article)

def test_open_meta_common():
    journal, article = create_journal_and_article()
    rating = Rating.create(journal=journal, free_to_read=True, source="manual")
    repository = Repository.create(name="Test Repo", source="manual")
    instance = Instance.create(article=article, repository=repository, free_to_read=True, source="manual")

    assert rating.free_to_read
    assert instance.free_to_read

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
