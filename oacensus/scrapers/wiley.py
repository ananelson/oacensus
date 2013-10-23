from oacensus.scraper import Scraper
import os
import urllib
import xlrd

class WileyScraper(Scraper):
    """
    Scraper for Wiley journals.
    """
    aliases = ['wiley']
    _settings = {
            'url' : "http://wileyonlinelibrary.com/journals-list",
            'header-row' : ("Row in spreadsheet containing column headers.", 5),
            'data-file' : "wiley-journals.xls"
            }

    def scrape(self):
        filepath = os.path.join(self.work_dir(), self.setting('data-file'))
        urllib.urlretrieve(self.setting('url'), filepath)

    def parse(self):
        from oacensus.models import JournalList
        from oacensus.models import Publisher
        from oacensus.models import Journal

        filepath = os.path.join(self.cache_dir(), self.setting('data-file'))

        wb = xlrd.open_workbook(filepath, on_demand=True)
        sheet = wb.sheet_by_index(0)

        headers = sheet.row_values(self.setting('header-row'), 0, 15)

        issn_col = 1
        eissn_col = 2
        doi_col = 3
        title_col = 4
        subject_col = 8

        assert headers[issn_col] == "Print ISSN"
        assert headers[eissn_col] == "Electronic ISSN"
        assert headers[doi_col] == "Journal DOI"
        assert headers[title_col] == "Title"
        assert headers[subject_col] == "General Subject Category"

        journal_list = JournalList.create(name="Wiley Journals")
        publisher = Publisher.create(name="Wiley")

        start = self.setting('header-row') + 1
        found_end = False
        max_row = 65000

        for i in range(start, max_row):
            if i % 100 == 0:
                print "  processing row", i

            try:
                values = sheet.row_values(i, 0, 10)
            except IndexError:
                found_end = True
                break

            journal = Journal.create(
                source = self.alias,
                issn = values[issn_col],
                eissn = values[eissn_col],
                doi = values[doi_col],
                title = values[title_col],
                subject = values[subject_col],
                publisher = publisher
                )

            journal_list.add_journal(journal)

        if not found_end:
            raise Exception("did not find end, may need to increase max")

        print journal_list
