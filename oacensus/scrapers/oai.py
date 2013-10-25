from oacensus.scraper import Scraper
from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, oai_dc_reader
import cPickle as pickle
import os
import datetime

class OAIPMH(Scraper):
    """
    Scrape OAI/PMH repositories.

    This has some ORA (Oxford University Research Archive) specific stuff in here.
    """
    aliases = ['oai']

    _settings = {
            'data-file' : (
                'internal data file for storage',
                'oai.pickle'
                ),
            'base-api-url' : (
                "Base url of repository.",
                "http://ora.ouls.ox.ac.uk:8080/fedora/oai"
                ),
            'base-objects-url' : (
                "URL at which objects can be accessed by uuid.",
                "http://ora.ouls.ox.ac.uk/objects/"
                ),
            'from' : ( "'from' prameter", datetime.datetime(2013, 1, 1)),
            'until' : ( "'until' prameter", datetime.datetime(2013, 12, 31)),
            'set' : (
                "'set' parameter to be passed in query.", None
                )
            }

    def scrape(self):
        registry = MetadataRegistry()
        registry.registerReader('oai_dc', oai_dc_reader)
        url = self.setting('base-api-url')
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

        if oai_from:
            kwargs['from_'] = oai_from

        if oai_until:
            kwargs['until'] = oai_until

        records = [r for r in client.listRecords(metadataPrefix='oai_dc', **kwargs)]

        data_filepath = os.path.join(self.work_dir(), self.setting('data-file'))
        with open(data_filepath, 'wb') as f:
            print "  picking", len(records), "records"
            pickle.dump(records, f)

    def parse(self):
        data_filepath = os.path.join(self.cache_dir(), self.setting('data-file'))
        with open(data_filepath, 'rb') as f:
            records = pickle.load(f)

        for record in records:
            header, meta, _ = record
            m = meta.getMap()

            # Skip over theses.
            if u'thesis          ' in m['type']:
                continue

            title = m['title'][0].strip()
            date = m['date'][0].strip()

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

            print "authors", "; ".join(author.strip() for author in m['creator'])
            print "title", title
            print "object url", object_url
            print "license", license
            print "date", date

        # now what? match on titles?
        # https://pypi.python.org/pypi/jellyfish/0.1.2
        # http://nltk.googlecode.com/svn/trunk/doc/api/nltk.metrics.distance-module.html
