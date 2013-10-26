from oacensus.report import Report
import datetime
import os
import xlwt
import inflection

class ExcelDump(Report):
    """
    Dump all database models to a single excel workbook.
    """
    aliases = ['excel']
    _settings = {
            'filename' : ("Name of file to write excel dump to.", "dump.xls"),
            'date-format-string' : ( "Excel style date format string.", "D-MMM-YYYY")
            }

    def run(self):
        from oacensus.models import Article
        from oacensus.models import Journal
        from oacensus.models import Publisher

        from oacensus.models import ModelBase

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

        for klass in [Article, Journal, Publisher]:
            ws = workbook.add_sheet(klass.__name__)
            for i, instance in enumerate(klass.select()):
                keys = sorted(instance.__dict__['_data'])

                if i == 0:
                    # print headers
                    for j, k in enumerate(keys):
                        heading = inflection.titleize(k)
                        ws.write(i, j, heading, bold_style)

                for j, key in enumerate(keys):
                    fmt = None
                    value = getattr(instance, key)

                    if isinstance(value, ModelBase):
                        value = unicode(value)
                    elif isinstance(value, datetime.date):
                        fmt = date_style
                    else:
                        # print type(value)
                        pass

                    if fmt:
                        ws.write(i+1, j, value, fmt)
                    else:
                        ws.write(i+1, j, value)

        workbook.save(filename)
        print "  database contents written to %s" % filename
