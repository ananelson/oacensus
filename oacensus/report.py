from cashew import Plugin, PluginMeta
from oacensus.constants import defaults

class Report(Plugin):
    """
    Parent class for reports.
    """
    __metaclass__ = PluginMeta

    def __init__(self, opts=None):
        if opts:
            self._opts = opts
        else:
            self._opts = defaults

    def run(self):
        raise NotImplementedError()
