import urlparse
import requests

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
