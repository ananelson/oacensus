from cashew import Plugin, PluginMeta
from oacensus.models import Journal
from oacensus.utils import defaults
import hashlib
import os
import shutil
import chardet
import codecs
from dateutil import rrule, relativedelta
from datetime import datetime

class Scraper(Plugin):
    """
    Parent class for scrapers.
    """
    __metaclass__ = PluginMeta

    _settings = {
            'cache': ("Location to copy cache files from.", None),
            'encoding' : ("Which encoding to use. Can be 'chardet'.", None)
            }

    def __init__(self, opts=None):
        """
        Initialize with command line options (distinct from scraper settings).
        """
        if opts:
            self._opts = opts
        else:
            self._opts = defaults

    def decode_encoded(self, text):
        encoding = self.setting('encoding')
        if encoding is None:
            return text
        elif encoding == 'chardet':
            detected_encoding = chardet.detect(text)['encoding']
            return codecs.decode(text, detected_encoding)
        else:
            return codecs.decode(text, encoding)

    def print_progress(self, msg):
        if self._opts['progress']:
            print msg

    def hash_settings(self):
        """
        Dictionary of settings which should be used to construct hash.
        """
        return self.setting_values()

    def hashstring(self, settings):
        """
        Return hash settings in consistent hashable format.
        """
        return ",".join("%s:%s" % (k, settings[k]) for k in sorted(settings))

    def hashcode(self, settings):
        """
        Turn hash string into hash code.
        """
        return hashlib.md5(self.hashstring(settings)).hexdigest()

    def run(self):
        print self.cache_dir()
        if self.is_scraped_content_cached():
            print "  scraped data is already cached"
        else:
            self.reset_work_dir()
            if self.setting('cache') is not None:
                print "  using cache location %s..." % self.setting('cache')
                shutil.copytree(self.setting('cache'), self.cache_dir())
            else:
                print "  calling scrape method..."
                self.scrape()
                self.copy_work_dir_to_cache()

        print "  calling process method..."
        return self.process()

    def cache_dir(self):
        """
        Location of this object's cache directory.
        """
        return os.path.join(self._opts['cachedir'], self.hashcode(self.hash_settings()))

    def work_dir(self):
        """
        Location of this object's work directory.
        """
        return os.path.join(self._opts['workdir'], self.hashcode(self.hash_settings()))

    def copy_work_dir_to_cache(self):
        """
        When work is completed, populated working directory is moved to cache.
        """
        shutil.move(self.work_dir(), self.cache_dir())
        assert self.is_scraped_content_cached()

    def create_cache_dir(self):
        os.makedirs(self.cache_dir())

    def remove_cache_dir(self):
        assert os.path.abspath(".") in os.path.abspath(self.cache_dir())
        shutil.rmtree(self.cache_dir(), ignore_errors=True)

    def is_scraped_content_cached(self):
        return os.path.exists(self.cache_dir())

    def reset_work_dir(self):
        """
        Remove any old working content and ensure an empty work dir exists.
        """
        assert os.path.abspath(".") in os.path.abspath(self.work_dir())
        shutil.rmtree(self.work_dir(), ignore_errors=True)
        os.makedirs(self.work_dir())

    def scrape(self):
        """
        Fetch remote data and store it in the local cache.
        """
        raise NotImplementedError()

    def process(self):
        """
        Working from the local cache, process data & add to db.
        """
        raise NotImplementedError()

class ArticleScraper(Scraper):
    """
    Scrapers which generate articles.
    """
    aliases = ['articlescraper']
    _settings = {
            "start-month" : ("Month in yyyy-mm format.", None),
            "end-month" : ("Month in yyyy-mm format.", None)
            }

    def parse_month(self, param_name):
        datestring = self.setting(param_name)
        if datestring is None:
            if "end" in param_name:
                return None
            else:
                raise Exception("%s must be provided in YYYY-MM format" % param_name)
        return datetime.strptime("%s-01" % datestring, "%Y-%m-%d")

    def period_hash_settings(self, period):
        settings = self.hash_settings()
        settings.update({'period' : period.strftime("%Y-%m")})
        return settings

    def period_hashcode(self, period):
        return self.hashcode(self.period_hash_settings(period))

    def periods(self):
        """Iterator for each month between start and end months."""
        start_month = self.parse_month("start-month")
        end_month = self.parse_month("end-month")

        a_month_ago = datetime.now() + relativedelta.relativedelta(months = -1)
        start_of_previous_month = datetime.strptime("%s-01" % a_month_ago.strftime("%Y-%m"), "%Y-%m-%d")

        if end_month is None:
            end_month = start_of_previous_month
        elif end_month < start_month:
            raise Exception("Start month %s must be before end month %s" % (start_month, end_month))
        elif end_month > start_of_previous_month:
            raise Exception("End month %s must be before the current date." % end_month)

        return rrule.rrule(rrule.MONTHLY, dtstart=start_month, until=end_month)

    def period_cache_dir(self, period):
        return os.path.join(self._opts['cachedir'], self.period_hashcode(period))

    def is_period_cached(self, period):
        return os.path.exists(self.period_cache_dir(period))

    def is_period_stored(self, period):
        return False

    def scrape(self):
        for period in self.periods():
            if not self.is_period_cached(period):
                self.scrape_period(period)

    def process(self):
        for period in self.periods():
            if not self.is_period_stored(period):
                self.process_period(period)

class ArticleInfoScraper(Scraper):
    """
    Scrapers which add metadata to existing articles.
    """
    def scrape(self):
        pass

class JournalScraper(Scraper):
    """
    Scrapers which generate or add metadata to journals.
    """
    _settings = {
            "add-new-journals" : ("Whether to create new Journal instances if one doesn't already exist.", False),
            "update-journal-fields" : ("Whitelist of fields which should be applied when updating an existing journal.", []),
            "limit" : ("Limit of journals to process (for testing/dev)", None)
            }

    def create_or_modify_journal(self, issn, args, journal_list=None):
        decoded_args = {}
        for k, v in args.iteritems():
            if isinstance(v, basestring):
                decoded_args[k] = self.decode_encoded(v)
            else:
                decoded_args[k] = v

        journal = Journal.by_issn(issn)
        if journal is None and self.setting('add-new-journals'):
            journal = self.create_new_journal(issn, decoded_args)
            self.print_progress("Created new journal: %s" % journal)
        elif journal is not None:
            journal = self.modify_existing_journal(journal, issn, decoded_args)
            self.print_progress("Modified existing journal: %s" % journal)

        if journal_list is not None and journal is not None:
            journal_list.add_journal(journal)

        return journal

    def create_new_journal(self, issn, args):
        args['issn'] = issn
        args['source'] = self.alias
        return Journal.create(**args)

    def modify_existing_journal(self, journal, issn, args):
        update_journal_fields = self.setting('update-journal-fields')
        for k, v in args.iteritems():
            if k in update_journal_fields:
                setattr(journal, k, v)
        journal.save()
        return journal
