from cashew import Plugin, PluginMeta
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, MONTHLY
from oacensus.models import Article
from oacensus.models import ArticleList
from oacensus.models import ArticleListMembership
from oacensus.models import Instance
from oacensus.models import Journal
from oacensus.models import JournalList
from oacensus.models import JournalListMembership
from oacensus.models import Publisher
from oacensus.models import Rating
from oacensus.models import model_classes
from oacensus.utils import defaults
from oacensus.utils import relativedelta_units
import chardet
import codecs
import hashlib
import os
import os.path
import shutil
import sys

UTF8Writer = codecs.getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)

class Scraper(Plugin):
    """
    Parent class for scrapers.
    """
    __metaclass__ = PluginMeta

    _settings = {
            'cache-expires' : ("Number of units after which to expire cache files.", None),
            'cache-expires-units' : ("Unit of time for cache-expires. Options are: years, months, weeks, days, hours, minutes, seconds, microseconds", "days"),
            'encoding' : ("Which encoding to use. Can be 'chardet'.", None),
            'no-hash-settings' : ("Settings to exclude from hash calculations.", [])
            }

    def __init__(self, opts=None):
        """
        Initialize with command line options (distinct from scraper settings).
        """
        if opts:
            self._opts = opts
        else:
            self._opts = defaults

    def create_dummy_db_entry(self):
        ArticleList.create(
                name="Dummy Entry",
                source=self.db_source(),
                log="Created this dummy entry so scraper will count as 'stored'.")
        
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
        return dict((k, v)
                for k, v in self.setting_values().iteritems()
                if not k in self.setting('no-hash-settings'))

    def hashstring(self, settings):
        """
        Return hash settings in consistent hashable format.
        """
        return ",".join("%s:%s" % (k, settings[k]) for k in sorted(settings))

    def hashcode(self, settings = None):
        """
        Turn hash string into hash code.
        """
        if settings is None:
            settings = self.hash_settings()
        return hashlib.md5(self.hashstring(settings)).hexdigest()

    def run(self):
        self.print_progress(self.cache_dir())
        if self.is_data_cached():
            self.print_progress("  scraped data is already cached")
        else:
            # Make sure database is cleared of old data.
            self.remove_stored_data()
            assert not self.is_data_stored()

            self.reset_work_dir()
            self.print_progress("  calling scrape method...")
            self.scrape()
            self.copy_work_dir_to_cache()

        if self.is_data_stored():
            self.print_progress("  data is already stored")
        else:
            self.print_progress("  calling process method...")
            try:
                return self.process()
            except ArticleScraperException:
                # don't need to clean up db here, it's already done in
                # ArticleScraper for the affected period
                raise
            except Exception:
                self.remove_stored_data()
                raise

    # Cache and Work Dirs

    def cache_dir(self):
        return os.path.join(self._opts['cachedir'], self.hashcode())

    def work_dir(self):
        return os.path.join(self._opts['workdir'], self.hashcode())

    def copy_work_dir_to_cache(self):
        """
        When work is completed, populated working directory is moved to cache.
        """
        shutil.move(self.work_dir(), self.cache_dir())
        assert self.is_data_cached()

    def create_work_dir(self):
        os.makedirs(self.work_dir())

    def create_cache_dir(self):
        os.makedirs(self.cache_dir())

    def remove_cache_dir(self):
        assert os.path.abspath(".") in os.path.abspath(self.cache_dir())
        shutil.rmtree(self.cache_dir(), ignore_errors=True)

    def db_source(self):
        return self.safe_setting('source', self.alias)

    def remove_stored_data(self):
        source = self.db_source()
        for klass in model_classes:
            klass.delete_all_from_source(source)

    def is_data_cached(self):
        try:
            mtime = os.path.getmtime(self.cache_dir())
            cache_expires = self.setting('cache-expires')
            if cache_expires is None:
                return True
            else:
                cache_last_modified = datetime.fromtimestamp(mtime)
                units = self.setting('cache-expires-units')
                cache_delta = relativedelta_units(cache_expires, units)
                if cache_last_modified < datetime.now() - cache_delta:
                    print "clearing cache since content has expired"
                    self.remove_cache_dir()
                    self.remove_stored_data()
                    return False
                else:
                    return True
        except OSError as e:
            if "No such file or directory" in e:
                return False
            else:
                raise

    def is_data_stored(self):
        source = self.db_source()
        return any(klass.exist_records_from_source(source) for klass in model_classes)

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

class ArticleScraperException(Exception):
    pass

class ArticleScraper(Scraper):
    """
    Base class for scrapers which parse articles.
    """
    aliases = ['articlescraper']
    _settings = {
            "start-period" : ("Period (month) in yyyy-mm format.", None),
            "end-period" : ("Period (month) in yyyy-mm format.", None),
            'no-hash-settings' : ["start-period", "end-period"]
            }

    def parse_month(self, param_name):
        "Returns a datetime for a yyyy-mm setting."
        datestring = self.setting(param_name)
        if datestring is None:
            if "end" in param_name:
                return None
            else:
                raise Exception("%s must be provided in YYYY-MM format" % param_name)
        return datetime.strptime("%s-01" % datestring, "%Y-%m-%d")

    def period_hash_settings(self, period_start_date):
        settings = self.hash_settings()
        settings.update({'period' : period_start_date.strftime("%Y-%m")})
        return settings

    def period_hashcode(self, start_date):
        return self.hashcode(self.period_hash_settings(start_date))

    def start_dates(self):
        "Return an iterator of start dates for monthly periods."
        start_month = self.parse_month("start-period")
        end_month = self.parse_month("end-period")

        a_month_ago = datetime.now() + relativedelta(months = -1)
        start_of_previous_month = datetime.strptime("%s-01" % a_month_ago.strftime("%Y-%m"), "%Y-%m-%d")

        if end_month is None:
            end_month = start_of_previous_month
        elif end_month < start_month:
            raise Exception("Start month %s must be before end month %s" % (start_month, end_month))
        elif end_month > start_of_previous_month:
            raise Exception("End month %s must be before the current date." % end_month)

        return rrule(MONTHLY, dtstart=start_month, until=end_month)

    def periods(self):
        "Return an iterator of period start and end dates."
        for i, start_date in enumerate(self.start_dates()):
            yield (start_date, start_date + relativedelta(months = 1))

    def period_cache_dir(self, start_date):
        return os.path.join(self._opts['cachedir'], self.period_hashcode(start_date))

    def period_work_dir(self, start_date):
        return os.path.join(self._opts['workdir'], self.period_hashcode(start_date))

    def copy_period_work_dir_to_cache(self, start_date):
        shutil.move(self.period_work_dir(start_date), self.period_cache_dir(start_date))
        assert self.is_period_cached(start_date)

    def create_period_work_dir(self, start_date):
        os.makedirs(self.period_work_dir(start_date))

    def create_period_cache_dir(self, start_date):
        os.makedirs(self.period_cache_dir(start_date))

    def reset_period_work_dir(self, start_date):
        """
        Remove any old working content and ensure an empty work dir exists.
        """
        work_dir = self.period_work_dir(start_date)
        assert os.path.abspath(".") in os.path.abspath(work_dir)
        shutil.rmtree(work_dir, ignore_errors=True)
        os.makedirs(work_dir)

    def remove_period_cache_dir(self, start_date):
        period_cache_dir = self.period_cache_dir(start_date)
        assert os.path.abspath(".") in os.path.abspath(period_cache_dir)
        shutil.rmtree(period_cache_dir, ignore_errors=True)

    def is_period_cached(self, start_date):
        "Is the period's scraped raw data available on the local file system?"
        return os.path.exists(self.period_cache_dir(start_date))

    def is_period_stored(self, start_date):
        "Is the period's data available in the local database?"
        raise NotImplementedError()

    def purge_period(self, start_date):
        "Purge the database records for the period."
        raise NotImplementedError()

    def scrape(self):
        if self.setting('cache-expires') is not None:
            raise Exception("Can't use cache-expires for periodic scrapers.")

        for start_date, end_date in self.periods():
            if not self.is_period_cached(start_date):
                self.reset_period_work_dir(start_date)
                self.scrape_period(start_date, end_date)
                self.copy_period_work_dir_to_cache(start_date)
            assert self.is_period_cached(start_date)

    def process(self):
        lists = []
        for start_date, end_date in self.periods():
            if not self.is_period_stored(start_date):
                assert self.is_period_cached(start_date)
                assert not self.is_period_stored(start_date)
                try:
                    article_list = self.process_period(start_date, end_date)
                    lists.append(article_list)
                except Exception as e:
                    print "An error has occurred while processing period %s, cleaning up DB so you can try again later" % start_date
                    self.purge_period(start_date)
                    assert not self.is_period_stored(start_date)
                    raise ArticleScraperException(str(e))
            assert self.is_period_stored(start_date)

        return lists

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
        journal = Journal.by_issn(issn)
        if journal is None and self.setting('add-new-journals'):
            journal = self.create_new_journal(issn, args)
            self.print_progress("Created new journal: %s" % journal)
        elif journal is not None:
            journal = self.modify_existing_journal(journal, issn, args)
            self.print_progress("Modified existing journal: %s" % journal)

        if journal_list is not None and journal is not None:
            journal_list.add_journal(journal, self.safe_setting('source', self.db_source()))

        return journal

    def create_new_journal(self, issn, args):
        args['issn'] = issn
        args['source'] = self.db_source()
        return Journal.create(**args)

    def modify_existing_journal(self, journal, issn, args):
        update_journal_fields = self.setting('update-journal-fields')
        for k, v in args.iteritems():
            if k in update_journal_fields:
                setattr(journal, k, v)
        journal.save()
        return journal
