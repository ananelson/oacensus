from jinja2 import FileSystemLoader
from oacensus.report import Report
import jinja2
import os
import shutil

cur_dir = os.path.abspath(os.path.dirname(__file__))

class JinjaReport(Report):
    """
    Base class for reports which use jinja templating.
    """
    _settings = {
            'template-file' : ("Path to template file.", None),
            'output-dir' : ("Directory to output report. Should start with 'report-' prefix", None),
            'output-file' : ("Name of report.", "output.html"),
            'template-dirs' : (
                "Locations to look for template files.",
                ['.', os.path.join(cur_dir, 'templates')]
                )
            }

    def template_data(self):
        """
        Return a dictionary whose keys will be available in the jinja template.
        """
        return {
                'foo' : 123
                }

    def do_other_actions(self):
        """
        Do other stuff like generate plots.
        """
        pass

    def process_jinja_template(self):
        dirs = self.setting('template-dirs')
        loader = FileSystemLoader(dirs)
        env = jinja2.Environment(loader=loader)
        template = env.get_template(self.setting('template-file'))
        template_data = self.template_data()
        output_filepath = os.path.join(self.setting('output-dir'), self.setting('output-file'))
        template.stream(template_data).dump(output_filepath, encoding="utf-8")

    def setup_output_dir(self):
        assert self.setting('output-dir'), "output-dir setting must be provided"
        assert self.setting('output-dir').startswith('report-'), "output-dir should start with report- prefix"
        shutil.rmtree(self.setting('output-dir'), ignore_errors=True)
        os.makedirs(self.setting('output-dir'))

    def run(self):
        self.setup_output_dir()
        self.do_other_actions()
        self.process_jinja_template()

