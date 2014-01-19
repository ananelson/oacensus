from oacensus.models import Article
from oacensus.models import Journal
from oacensus.models import JournalList
from oacensus.models import JournalListMembership

def test_find_or_create():
    journal = Journal.create_or_update_by_issn({"issn" : "abc", "title" : "The Journal", "source" : "test"})
    assert journal.title == "The Journal"
    journal = Journal.create_or_update_by_issn({"issn" : "abc", "title" : "The Updated Journal"})
    assert journal.title == "The Updated Journal"

def test_article():
    pmid = "ABC1234"

    article = Article()
    article.title = "This Is A Title"
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
    article.source = "test"
    article.title = "My Article"
    article.save()

    assert article.journal.title == "My Journal"

def test_journal_list():
    journal_list = JournalList()
    journal_list.name = "Open Access Journals"
    journal_list.save()

    journal = Journal()
    journal.title = "An Open Access Journal"
    journal.source = "test"
    journal.save()

    membership = JournalListMembership()
    membership.journal_list = journal_list
    membership.journal = journal
    membership.save()

    assert journal_list.journals()[0] == journal

def test_add_journal_to_list():
    journal_list = JournalList()
    journal_list.name = "Open Access Journals"
    journal_list.save()

    journal = Journal()
    journal.title = "An Open Access Journal"
    journal.source = "test"
    journal.save()

    journal_list.add_journal(journal)
    assert journal_list.journals()[0] == journal
