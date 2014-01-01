from oacensus.reports.jinja_reports import JinjaReport
import hashlib
import datetime
import json

try:
    import matplotlib.pyplot as plt
    import numpy
    import scipy
    IS_AVAILABLE = True
except ImportError:
    print "matplitlib, numpy, scipy are required for PersonalOpenness"
    IS_AVAILABLE = False

class InstitutionalReport(JinjaReport):
    """
    Generate an institutional openness report
    """
    aliases = ['institution']

    _settings = {
            'output-dir' : 'report-institutions',
            'output-file' : 'cambridge.html',
            'template-file' : 'institution.html'
            }

    def is_active(self):
        return IS_AVAILABLE

    def draw_graph(self, filepath, vals):

        plt.figure(figsize=(5,3), dpi=100)
        ax = plt.subplot(1, 1, 1)

        years = vals[0]
        total_articles = vals[1]
        have_dois = vals[2]
        cc_by = vals[3]
        doaj = vals[4]

        index = numpy.arange(len(years))
        bar_width = 0.35

        totals = plt.bar(index, total_articles, bar_width,
                        color = 'b',
                        label = "Total articles"
                        )

        with_dois = plt.bar(index + bar_width, have_dois, bar_width,
                            color = 'r',
                            label = "Have DOIs"
                            )
        plt.xlabel('Year')
        plt.ylabel('# Articles')
        plt.xticks(index + bar_width, years)
        plt.legend()
        plt.savefig(filepath)

    def format_data(self, vals):
        data = []
        for i in range(len(vals[0])):
            data.append({
                        'year' : vals[0][i],
                        'total' : vals[1][i],
                        'have_dois' : vals[2][i],
                        'are_ccby' : vals[3][i],
                        'in_doaj' : vals[4][i]
                        }
                        )
        return data


    def template_data(self):
        from oacensus.models import Article

        articles = [a for a in Article.select()]
        print "length:", len([a for a in articles])
        years = [2010, 2011, 2012, 2013]
        total_articles = []
        have_dois = []
        cc_by = []
        doaj = []

        for year in years:
            startdate = datetime.datetime(year, 1, 1)
            enddate = datetime.datetime(year, 12, 31, 23, 59, 59)
            yr_articles = [a for a in articles if (
                                    a.publication_date > startdate |
                                    a.publication_date < enddate
                                                )
                                                ]
            n_articles = year# len([a for a in yr_articles])
            n_doi = year#len([a for a in yr_articles if a.doi])
            n_cc_by = year#len([a for a in yr_articles if a.open_access])
            n_doaj = year#len([a for a in yr_articles if a.journal.open_access])

            total_articles.append(n_articles)
            have_dois.append(n_doi)
            cc_by.append(n_cc_by)
            doaj.append(n_doaj)

        vals = [years, total_articles, have_dois, cc_by, doaj]
        data = self.format_data(vals)
        graph_file = "plot-%s.png" % hashlib.md5('uwe-articles').hexdigest()
        graph_path = self.file_in_output_dir(graph_file)
        self.draw_graph(graph_path, vals)
        print data
        return {
                'data' : data,
                'graph' : graph_file
                }