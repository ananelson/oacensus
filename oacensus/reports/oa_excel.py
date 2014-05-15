from oacensus.models import Article
from oacensus.models import ModelBase
from oacensus.report import Report
import datetime
import inflection
import inspect
import os
import xlwt

class OAExcel(Report):
    """
    An excel-based openness report.
    """

    aliases = ['openness-excel']

    _settings = {
            'filename' : ("Name of file to write excel dump to.", "openness.xls"),
            "sheet-name" : ("Name of worksheet.", "Openness"),
            'date-format-string' : ( "Excel style date format string.", "D-MMM-YYYY"),
            "fields" : ("Fields to include in report.", [
                "id", "title", "doi", "journal.title", "publisher.name", "is_free_to_read", "license_name", "license_source", "log", "journal.issn", "licenses_str", "ratings_str"
                ])
            }

    def run(self):
        date_style = xlwt.XFStyle()
        date_style.num_format_str = self.setting('date-format-string')

        bold_font = xlwt.Font()
        bold_font.bold = True

        bold_style = xlwt.XFStyle()
        bold_style.font = bold_font

        filename = self.setting('filename')
        if os.path.exists(filename):
            os.remove(filename)

        workbook = xlwt.Workbook()
        ws = workbook.add_sheet("Openness")

        keys = self.setting('fields')

        # Write Headers
        for j, k in enumerate(keys):
            heading = inflection.titleize(k)
            ws.write(0, j, heading, bold_style)

        for i, article in enumerate(Article.select()):
            for j, key in enumerate(keys):
                if key.startswith("journal."):
                    value = getattr(article.journal, key.replace("journal.", ""))
                elif key.startswith("publisher."):
                    value = getattr(article.journal.publisher, key.replace("publisher.", ""))
                else:
                    value = getattr(article, key)

                fmt = None

                if isinstance(value, ModelBase):
                    value = unicode(value)
                elif isinstance(value, datetime.date):
                    fmt = date_style
                elif inspect.ismethod(value):
                    value = value()
                else:
                    pass

                if fmt:
                    ws.write(i+1, j, value, fmt)
                else:
                    ws.write(i+1, j, value)

        workbook.save(filename)
        print "  openness report written to %s" % filename
