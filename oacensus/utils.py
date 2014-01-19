import urlparse
import requests
import datetime

defaults = {
    'cachedir' : '.oacensus/cache/',
    'config' : 'oacensus.yaml',
    'dbfile' : 'oacensus.sqlite3',
    'profile' : False,
    'progress' : False,
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

def parse_datestring_to_date(date_string):
    """
    Utility function for parsing datestrings in various formats
    """

    date = None
    for format in [ '%Y',
                    '%Y-%m',
                    '%Y-%m-%d',
                    '%d-%m-%Y',
                    '%d/%m/%Y',
                    '%Y-%b',
                    '%b-%Y',
                    '%b %Y',
                    '%Y %b',
                    '%d %b %Y',
                    '%b %d %Y',
                    '%d %B %Y',
                    '%B %d %Y'
                    ]:
        try:
            date = datetime.datetime.strptime(date_string, format)
            break
        except ValueError:
            pass

    return date



