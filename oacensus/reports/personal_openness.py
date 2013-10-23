from oacensus.reports.jinja_reports import JinjaReport

class PersonalOpenness(JinjaReport):
    """
    Generate a personal openness report.
    """
    aliases = ['personal-openness']

    _settings = {
            'output-dir' : "report-openness",
            'output-file' : 'index.html',
            'template-file' : 'openness.html'
        }

    def template_data(self):
        from oacensus.models import ArticleList
        return {
                'foo' : 456,
                'article_lists' : ArticleList.select()
                }
