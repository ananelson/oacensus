from jinja2 import FileSystemLoader
from oacensus.report import Report
import jinja2
import os
import shutil

cur_dir = os.path.abspath(os.path.dirname(__file__))

class Jinja(Report):
    """
    Base class for reports which use jinja templating.
    """
    _settings = {
            'template-file' : ("Path to template file.", None),
            'output-dir' : ("Directory to output report.", "."),
            'output-file' : ("Name of report.", "output.html"),
            'template-dirs' : (
                "Locations to look for template files.",
                ['.', os.path.join(cur_dir, 'templates')]
                )
            }

    def template_data(self):
        return {
                'foo' : 123
                }

    def run(self):
        dirs = self.setting('template-dirs')
        loader = FileSystemLoader(dirs)
        env = jinja2.Environment(loader=loader)
        template = env.get_template(self.setting('template-file'))
        template_data = self.template_data()
        output_filepath = os.path.join(self.setting('output-dir'), self.setting('output-file'))

        shutil.rmtree(self.setting('output-dir'), ignore_errors=True)
        os.makedirs(self.setting('output-dir'))

        template.stream(template_data).dump(output_filepath, encoding="utf-8")

from oacensus.models import ArticleList
class PersonalOpenness(Jinja):
    """
    Generate a personal openness report.
    """
    aliases = ['personal-openness']
    _settings = {
            'output-dir' : "openness",
            'output-file' : 'index.html',
            'template-file' : 'openness.html'
            }

    def template_data(self):
        return {
                'foo' : 456,
                'article_lists' : ArticleList.select()
                }
