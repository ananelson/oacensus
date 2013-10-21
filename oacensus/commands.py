from modargs import args
from oacensus.constants import defaults
from oacensus.scraper import Scraper
from oacensus.report import Report
import sys
import yaml

default_command = 'help'
mod = sys.modules[__name__]
prog = 'oacensus'

import oacensus.load_plugins

s = '    '

def run():
    """
    Main entry point. Calls python modargs to run the requested command.
    """
    args.parse_and_run_command(sys.argv[1:], mod, default_command=default_command)

def help_command(on=False):
    args.help_command(prog, mod, default_command, on)

def scrapers_command():
    """
    List the available scraper plugins.
    """
    nodoc = ['aliases', 'help']

    for instance in Scraper:
        print "\n"
        print s, "alias:", instance.alias
        for line in instance.setting('help').splitlines():
            print s, line
        print ""
        for setting_name in sorted(instance._instance_settings):
            if setting_name in nodoc:
                continue
            setting_info = instance._instance_settings[setting_name]
            print "%s %s: %s (%s)" % (s*2, setting_name, setting_info[0], setting_info[1])

    print "\n"

def run_command(
        reports=defaults['reports'], # Reports to run.
        config=defaults['config'], # YAML file to read configuration from.
        cachedir=defaults['cachedir'], # Directory to store cached scraped data.
        workdir=defaults['workdir'], # Directory to store temp working directories.
        ):

    with open(config, 'r') as f:
        conf = yaml.safe_load(f.read())

    for item in conf:
        if isinstance(item, basestring):
            alias = item
            settings = {}
        elif isinstance(item, dict):
            assert len(item.keys()) == 1
            alias = item.keys()[0]
            settings = item[alias]

            if not alias in Scraper.plugins:
                msg = "Must define a parent of new alias."
                assert "parent" in settings, msg

                parent_alias = settings['parent']
                msg = "Parent %s not found in existing plugins." % parent_alias
                assert parent_alias in Scraper.plugins, msg

                parent = Scraper.plugins[parent_alias]
                class_or_class_name, parent_settings = parent
                new_settings = parent_settings
                new_settings.update(settings)
                Scraper.register_plugin(alias, class_or_class_name, new_settings)

        else:
            raise Exception("Unexpected type %s" % type(item))

        print "running", alias
        scraper = Scraper.create_instance(alias, locals())
        scraper.update_settings(settings)
        scraper.run()

    for report_alias in reports.split():
        report = Report.create_instance(report_alias)
        report.run()
