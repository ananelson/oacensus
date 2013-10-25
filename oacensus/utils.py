defaults = {
    'cachedir' : '.oacensus/cache/',
    'config' : 'oacensus.yaml',
    'dbfile' : 'oacensus.sqlite3',
    'profile' : False,
    'progress' : False,
    'reports' : '',
    'workdir' : '.oacensus/work/'
}

def trunc(s, length=40):
    if len(s) < length:
        return s
    else:
        return s[0:length] + "..."
