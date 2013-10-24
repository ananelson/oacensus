defaults = {
    'dbfile' : 'oacensus.sqlite3',
    'progress' : False,
    'reports' : '',
    'config' : 'oacensus.yaml',
    'cachedir' : '.oacensus/cache/',
    'workdir' : '.oacensus/work/'
}

def trunc(s, length=40):
    if len(s) < length:
        return s
    else:
        return s[0:length] + "..."
