from oacensus.reports.jinja_reports import JinjaReport
import hashlib

try:
    import matplotlib.pyplot as plt
    import numpy
    import scipy
    IS_AVAILABLE = True
except ImportError:
    print "matplitlib, numpy, scipy are required for PersonalOpenness"
    IS_AVAILABLE = False

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

    def is_active(self):
        return IS_AVAILABLE

    def draw_dotplot(self, filepath, vals):
        plt.figure(figsize=(5,3), dpi=100)
        ax = plt.subplot(1, 1, 1)

        spines = ["bottom"]
        for loc, spine in ax.spines.iteritems():
            if loc not in spines:
                spine.set_color('none')

        ax.yaxis.set_tick_params(size=0)
        ax.yaxis.set_ticklabels(['Open Access', '', 'Have DOIs', '', 'All Articles'])

        ax.xaxis.set_ticks_position('bottom')
        ax.xaxis.grid(True)

        bars = [3.1,2.1,1.1]

        plt.plot(vals, bars, 'o')
        plt.hlines(bars, [0], vals, linestyles='solid', lw=1)

        plt.tight_layout()

        plt.savefig(filepath)

    def template_data(self):
        from oacensus.models import ArticleList
        orcid_lists = ArticleList.select().where(ArticleList.name % "ORCID*")

        lists = []
        for l in orcid_lists:
            n_articles = len([a for a in l.articles()])
            n_articles_with_dois = len([a for a in l.articles() if a.doi])
            n_open_access_articles = len([a for a in l.articles() if a.open_access])
            data = [n_articles, n_articles_with_dois, n_open_access_articles]

            dotplot_file = "plot-%s.png" % hashlib.md5(l.name).hexdigest()
            dotplot_path = self.file_in_output_dir(dotplot_file)
            self.draw_dotplot(dotplot_path, data)

            lists.append( (l, dotplot_file,) )

        return {
                'article_lists' : lists
                }
