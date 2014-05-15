from dateutil.relativedelta import relativedelta
import requests
import urlparse
import os

nihm_name = "National Institutes of Health and Medicine"
pmc_name = "PubMed Central"
pubmed_name = "PubMed"

project_root = os.path.dirname(__file__)

defaults = {
    'cachedir' : '.oacensus/cache/',
    'config' : 'oacensus.yaml',
    'dbfile' : 'oacensus.sqlite3',
    'profile' : False,
    'progress' : True,
    'reports' : '',
    'workdir' : '.oacensus/work/'
}

def urlretrieve(url, params, filepath):
    """
    Write url reusults to a file, using python-requetss for nice handling of params.
    """
    result = requests.get(url, params=params, stream=True)
    with open(filepath, "wb") as f:
        for block in result.iter_content(1024):
            if not block:
                break
            f.write(block)

def trunc(s, length=40):
    if len(s) < length:
        return s
    else:
        return s[0:length] + "..."

def crossref_coins(crossref_info):
    return urlparse.urlparse(crossref_info['coins']).params

def parse_coins(raw_coins):
    return urlparse.parse_qs(raw_coins)

def parse_crossref_coins(crossref_info):
    return parse_coins(crossref_coins(crossref_info))

def relativedelta_units(interval, units):
    if units == 'days':
        return relativedelta(days = interval)
    elif units == 'years':
        return relativedelta(years = interval)
    elif units == 'months':
        return relativedelta(months = interval)
    elif units =='weeks':
        return relativedelta(weeks = interval)
    elif units == 'hours':
        return relativedelta(hours = interval)
    elif units == 'minutes':
        return relativedelta(minutes = interval)
    elif units == 'seconds':
        return relativedelta(seconds = interval)
    elif units == 'microseconds':
        return relativedelta(microseconds = interval)
    else:
        raise Exception("Invalid time unit %s" % units)

# http://docs.python.org/2/library/csv#csv-examples
import csv

def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')

def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.DictReader(utf_8_encoder(unicode_csv_data),
                            dialect=dialect, **kwargs)
    for row in csv_reader:
        # decode UTF-8 back to Unicode, cell by cell:
        yield dict( (name, unicode(cell, 'utf-8')) for name, cell in row.iteritems() )
