from dexy.plugin import Plugin
from dexy.plugin import PluginMeta
from oacensus.controller import CACHE_DIR
from oacensus.controller import WORK_DIR
import hashlib
import os
import shutil

class Scraper(Plugin):
    """
    Parent class for scrapers.
    """
    __metaclass__ = PluginMeta
    _settings = {}
    aliases = []

    def hash_settings(self):
        return self.setting_values()

    def hashstring(self):
        settings = self.hash_settings()
        return ",".join("%s:%s" % (k, settings[k]) for k in sorted(settings))

    def hashcode(self):
        return hashlib.md5(self.hashstring()).hexdigest()

    def run(self):
        self.remove_cache_dir()

        if not self.is_scraped_content_cached():
            self.reset_work_dir()
            self.scrape()
            self.copy_work_dir_to_cache()

        self.parse()

    def cache_dir(self):
        return os.path.join(CACHE_DIR, self.hashcode())

    def work_dir(self):
        return os.path.join(WORK_DIR, self.hashcode())

    def copy_work_dir_to_cache(self):
        shutil.move(self.work_dir(), self.cache_dir())
        assert self.is_scraped_content_cached()

    def create_cache_dir(self):
        os.makedirs(self.cache_dir())

    def remove_cache_dir(self):
        assert os.path.abspath(".") in os.path.abspath(self.cache_dir())
        shutil.rmtree(self.cache_dir(), ignore_errors=True)

    def reset_work_dir(self):
        assert os.path.abspath(".") in os.path.abspath(self.work_dir())
        shutil.rmtree(self.work_dir(), ignore_errors=True)
        os.makedirs(self.work_dir())

    def is_scraped_content_cached(self):
        return os.path.exists(self.cache_dir())

    def scrape(self):
        raise Exception("TODO implement")

    def parse(self):
        raise Exception("TODO implement")
