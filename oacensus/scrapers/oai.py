from oacensus.scraper import Scraper
from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, oai_dc_reader
import cPickle as pickle
import os
import datetime

class OAIPMH(Scraper):
    """
    Scrape OAI/PMH repositories.

    Not finished. Doesn't do anything right now.
    This has some ORA (Oxford University Research Archive) specific stuff in here.
    """
    aliases = ['oai']

    _settings = {
            'data-file' : ('internal data file for storage', 'oai.pickle'),
            'pmh-endpoint' : ("Base url of OAI PMH interface to repository.", None),
            'base-objects-url' : ("URL at which objects can be accessed by uuid.", None),
            'from' : ( "'from' parameter, in \"YYYY-MM-DD\" format", None ),
            'until' : ( "'until' parameter, in \"YYYY-MM-DD\" format", None ),
            'set' : ("'set' parameter", None)
          }

    def scrape(self):
        registry = MetadataRegistry()
        registry.registerReader('oai_dc', oai_dc_reader)
        url = self.setting('pmh-endpoint')
        client = Client(url, registry)

        print "  OAI Repository", url
        print "  Available sets:"
        for s in client.listSets():
            print "   ", s

        oai_set = self.setting('set')
        oai_from = self.setting('from')
        oai_until = self.setting('until')

        kwargs = {}

        if oai_set:
            kwargs['set'] = oai_set

        if oai_from is not None:
            date_args = [int(arg) for arg in oai_from.split("-")]
            kwargs['from_'] = datetime.datetime(*date_args)

        if oai_until is not None:
            date_args = [int(arg) for arg in oai_until.split("-")]
            kwargs['until'] = datetime.datetime(*date_args)

        records = [r for r in client.listRecords(metadataPrefix='oai_dc', **kwargs)]

        data_filepath = os.path.join(self.work_dir(), self.setting('data-file'))
        with open(data_filepath, 'wb') as f:
            print "  picking", len(records), "records"
            pickle.dump(records, f)

    def process(self):
        data_filepath = os.path.join(self.cache_dir(), self.setting('data-file'))
        with open(data_filepath, 'rb') as f:
            records = pickle.load(f)

        oai_info = []
        for record in records:
            header, meta, _ = record
            m = meta.getMap()

            # Skip over theses.
            if u'thesis          ' in m['type']:
                continue

            title = m['title'][0].strip()

            if len(m['date']) > 0:
                date = m['date'][0].strip()
            else:
                date = None

            license = None

            if m['rights']:
                license = m['rights'][0].strip()

            urn = None
            for identifier in m['identifier']:
                if identifier.startswith('uuid:'):
                    urn = identifier.strip()
                elif identifier.startswith('urn:uuid:'):
                    urn = identifier.replace('urn:', '').strip()
                else:
                    pass

            object_url = "%s%s" % (self.setting('base-objects-url'), urn)

            oai_info.append({
                "authors" : "; ".join(author.strip() for author in m['creator']),
                "title" : title,
                "url url" : object_url,
                "license" : license,
                "date" : date
            })

        # now what? try to match on titles?
        # https://pypi.python.org/pypi/jellyfish/0.1.2
        # http://nltk.googlecode.com/svn/trunk/doc/api/nltk.metrics.distance-module.html

        import jellyfish

        from oacensus.models import Article
        for article in Article.select():
            for info in oai_info:
                try:
                    jd = jellyfish.jaro_winkler(article.title, info['title'])

                    if jd > 0.8:
                        print article.title
                        print info['title']
                        print "Jaro Winkler Distance:", jd
                except (UnicodeDecodeError, UnicodeEncodeError):
                    pass
