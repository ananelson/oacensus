from oacensus.models import Article, Journal, Publisher, ArticleList, JournalList

def test_article():
    pmid = "ABC1234"

    article = Article()
    article.title = "This Is A Title"
    article.pubmed_id = pmid
    article.save()

    print Article.select()
