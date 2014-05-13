from oacensus.report import Report
from oacensus.models import model_classes

class TextDump(Report):
    """
    Dump all database models containing data to a text file.
    """
    aliases = ['textdump']
    _settings = {
            'filename' : ("Name of file to write dump to.", "dump.txt")
            }

    def run(self):
        data = ""

        for klass in model_classes:
            rows = klass.select()
            if rows.count() > 0:
                first = rows[0]
                keys = sorted(first.__dict__['_data'])

                # print class name
                data += klass.__name__ + "\n"

                # print header row
                data += "\t".join(keys) + "\n"

                # print data
                data += "\n".join(
                            "\t".join(str(getattr(row, key)) for key in keys)
                            for row in rows
                         )

                # add some spacing before the next section
                data += "\n\n"
       
        with open(self.setting('filename'), 'w') as f:
            f.write(data)
