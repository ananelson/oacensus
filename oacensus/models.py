from ado.model import Model

class Article(Model):
    FIELDS = {
            'title' : 'text'
            }
            
class Journal(Model):
    FIELDS = {
            'name' : 'text'
            }

class Publisher(Model):
    FIELDS = {
            'name' : 'text'
            }

class ArticleList(Model):
    FIELDS = {}

class JournalList(Model):
    FIELDS = {}
