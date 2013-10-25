from modargs import args
from oacensus.exceptions import UserFeedback
from oacensus.db import db
from oacensus.report import Report
from oacensus.scraper import Scraper
from oacensus.utils import defaults
import datetime
import os
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
    try:
        args.parse_and_run_command(sys.argv[1:], mod, default_command=default_command)
    except UserFeedback as e:
        sys.stderr.write("An %s has occurred. Stopping." % e.__class__.__name__)
        sys.stderr.write(str(e) + "\n")
        sys.exit(1)
    except KeyboardInterrupt:
        sys.stderr.write("interrupted!\n")
        sys.exit(1)

def help_command(on=False):
    args.help_command(prog, mod, default_command, on)

def scrapers_command(
        alias = '' # Optionally, only print help for the specified alias.
        ):
    """
    List the available scraper plugins.
    """
    nodoc = ['aliases', 'help']

    if alias:
        instances = [Scraper.create_instance(alias)]
    else:
        instances = Scraper

    for instance in instances:
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
        cachedir=defaults['cachedir'], # Directory to store cached scraped data.
        config=defaults['config'], # YAML file to read configuration from.
        dbfile=defaults['dbfile'], # Name of sqlite db file.
        profile=defaults['profile'], # Whether to run in profiler (dev only).
        progress=defaults['progress'], # Whether to show progress indicators.
        reports=defaults['reports'], # Reports to run.
        workdir=defaults['workdir'], # Directory to store temp working directories.
        ):

    start_time = datetime.datetime.now()

    if not os.path.exists(config):
        raise UserFeedback("Please provide a config file named '%s' or use --config option to specify a different filename." % config)

    with open(config, 'r') as f:
        conf = yaml.safe_load(f.read())

    if os.path.exists(dbfile):
        print "removing old db file", dbfile
        os.remove(dbfile)

    db.init(dbfile)

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

        if profile:
            import cProfile
            profile_filename = "%s-oacensus.prof" % alias
            print "running scraper with cProfile, writing data to", profile_filename
            cProfile.runctx("scraper.run()", None, locals(), profile_filename)
        else:
            scraper.run()

    print "scraping and parsing completed in", datetime.datetime.now() - start_time
    if reports:
        run_reports(reports)

def run_reports(reports):
    start_time = datetime.datetime.now()
    for report_alias in reports.split():
        print "running report %s" % report_alias
        report = Report.create_instance(report_alias)
        report.run()
    print "reports completed in", datetime.datetime.now() - start_time

def reports_command(
        dbfile = defaults['dbfile'], # db file to use for reports
        reports = defaults['reports'], # reports to run
        ):
    if not reports:
        print "Please specify some reports to run."

    db.init(dbfile)
    run_reports(reports)
