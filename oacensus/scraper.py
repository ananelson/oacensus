from cashew import Plugin, PluginMeta
from oacensus.utils import defaults
import hashlib
import os
import shutil

class Scraper(Plugin):
    """
    Parent class for scrapers.
    """
    __metaclass__ = PluginMeta

    _settings = {
            'cache': ("Location to copy cache files from.", None)
            }

    def __init__(self, opts=None):
        if opts:
            self._opts = opts
        else:
            self._opts = defaults

    def print_progress(self, msg):
        if self._opts['progress']:
            print msg

    def hash_settings(self):
        """
        Dictionary of settings which should be used to construct hash.
        """
        return self.setting_values()

    def hashstring(self):
        """
        Return hash settings in consistent hashable format.
        """
        settings = self.hash_settings()
        return ",".join("%s:%s" % (k, settings[k]) for k in sorted(settings))

    def hashcode(self):
        """
        Turn hash string into hash code.
        """
        return hashlib.md5(self.hashstring()).hexdigest()

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
        return os.path.join(self._opts['cachedir'], self.hashcode())

    def work_dir(self):
        """
        Location of this object's work directory.
        """
        return os.path.join(self._opts['workdir'], self.hashcode())

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
