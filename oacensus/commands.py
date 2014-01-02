from modargs import args
from oacensus.db import db
from oacensus.exceptions import ConfigFileFormatProblem
from oacensus.exceptions import UserFeedback
from oacensus.models import create_db_tables
from oacensus.report import Report
from oacensus.scraper import Scraper
from oacensus.utils import defaults
import datetime
import os
import sys
import yaml

default_cmd = 'help'
mod = sys.modules[__name__]
prog = 'oacensus'

import oacensus.load_plugins

s = '    '

def run():
    """
    Main entry point. Calls python modargs to run the requested command.
    """
    try:
        args.parse_and_run_command(sys.argv[1:], mod, default_command=default_cmd)
    except UserFeedback as e:
        sys.stderr.write("A %s has occurred. Stopping.\n\nError message:\n" % e.__class__.__name__)
        sys.stderr.write(str(e) + "\n")
        sys.exit(1)
    except KeyboardInterrupt:
        sys.stderr.write("interrupted!\n")
        sys.exit(1)

main_help = """
Available commands:

  help - Prints this help message or help for individual commands, scrapers or reports.
  list - List all available scrapers and reports.
  run  - Runs the oacensus tool.
  reports - Runs additional reports using data from the last run.

Run `oacensus help -on cmd` for detailed help on any of these commands.
"""

def help_command(
        on=False, # Provide a command name to get help for an individual command.
        scraper=False, # Provide a scraper alias to get help for an individual scraper.
        report=False, # Provide a report alias to get help for an individua lreport.
        ):
    """
    Command line documentation for the oacensus tool.

    Examples:

    `oacensus help -on run`
    `oacensus help -scraper oag`
    `oacensus help -report excel`
    """
    print ""
    if on:
        args.help_command(prog, mod, default_cmd, on)
    elif scraper:
        if scraper in Scraper.plugins:
            print "%s Scraper" % scraper
            instance = Scraper.create_instance(scraper)
            print_help_for_instance(instance)
        else:
            print "No scraper or report matching alias %s was found." % scraper
            sys.exit(1)
    elif report:
        if report in Report.plugins:
            print "%s Report" % report
            instance = Report.create_instance(report)
            print_help_for_instance(instance)
        else:
            print "No scraper or report matching alias %s was found." % report
            sys.exit(1)
    else:
        print main_help

def print_help_for_instance(instance):
    nodoc = ['aliases', 'help']
    print ""
    for line in instance.setting('help').splitlines():
        print line
    print ""
    print "Settings:"
    print ""
    for setting_name in sorted(instance._instance_settings):
        if setting_name in nodoc:
            continue
        setting_info = instance._instance_settings[setting_name]
        print "%s %s: %s (default value: %s)" % (s, setting_name, setting_info[0], setting_info[1])
    print ""

def list_command():
    """
    List the available scrapers and reports.
    """
    print "Scrapers:"
    print ""

    for scraper in Scraper:
        print "  ", scraper.alias

    print ""
    print "Reports:"
    print ""
    for report in Report:
        print "  ", report.alias

def run_command(
        cachedir=defaults['cachedir'], # Directory to store cached scraped data.
        config=defaults['config'], # YAML file to read configuration from.
        dbfile=defaults['dbfile'], # Name of sqlite db file.
        profile=defaults['profile'], # Whether to run in profiler (dev only).
        progress=defaults['progress'], # Whether to show progress indicators.
        reports=defaults['reports'], # Reports to run.
        workdir=defaults['workdir'], # Directory to store temp working directories.
        ):
    """
    Runs the oacensus scrapers specified in the configuration file.

    This is the main command for using the oacensus tool. It reads the
    configuration specified in YAML and runs the requested scrapers in order
    (using data from the cache if available). Data will be stored in a sqlite3
    database. After data has been processed and stored in the database, reports
    may be run which will present the data.
    """

    start_time = datetime.datetime.now()

    if not os.path.exists(config):
        raise UserFeedback("Please provide a config file named '%s' or use --config option to specify a different filename." % config)

    with open(config, 'r') as f:
        conf = yaml.safe_load(f.read())

    if os.path.exists(dbfile):
        print "removing old db file", dbfile
        os.remove(dbfile)

    db.init(dbfile)
    create_db_tables()

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

        print "running", alias, "scraper"
        scraper = Scraper.create_instance(alias, locals())

        try:
            scraper.update_settings(settings)
        except AttributeError as e:
            if str(e) == "'list' object has no attribute 'iteritems'":
                msg = "Don't use hyphens in the 2nd level of YAML config.\n"
                msg += "Correct format is\n- alias\n    key1: value1\n    key2: value2"
                raise ConfigFileFormatProblem(msg)

        if profile:
            import cProfile
            profile_filename = "%s-oacensus.prof" % alias
            print "running scraper with cProfile, writing data to", profile_filename
            cProfile.runctx("scraper.run()", None, locals(), profile_filename)
        else:
            scraper.run()

    print "scraping completed in", datetime.datetime.now() - start_time
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
