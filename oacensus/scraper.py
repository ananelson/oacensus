from cashew import Plugin, PluginMeta
from oacensus.constants import defaults
import hashlib
import os
import shutil

class Scraper(Plugin):
    """
    Parent class for scrapers.
    """
    __metaclass__ = PluginMeta

    def __init__(self, opts=None):
        if opts:
            self._opts = opts
        else:
            self._opts = defaults

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
        if not self.is_scraped_content_cached():
            self.reset_work_dir()
            print "  calling scrape method..."
            self.scrape()
            self.copy_work_dir_to_cache()
        else:
            print "  scraped data is already cached"

        print "  calling parse method..."
        self.parse()

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

    def parse(self):
        """
        Working from the local cache, parse data files and make content
        available for querying.
        """
        raise NotImplementedError()
