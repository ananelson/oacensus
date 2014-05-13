from oacensus.scrapers.tabularfile import TabularFile
import os
import xlrd

class ExcelFile(TabularFile):
    """
    Loads a list of articles from an Excel file, which may be local or at a remote URL.
    """

    aliases = ['excelarticles']

    _settings = { "data-file" : "work.xls" }

    def process(self):
        data_file = os.path.join(self.cache_dir(), self.setting('data-file'))
        book = xlrd.open_workbook(data_file)
        assert book.nsheets == 1
        sheet = book.sheet_by_index(0)
        headers = sheet.row(0)
        col_map = self.setting('column-mapping')
        attributes = [col_map.get(h.value) for h in headers]

        article_list = self.create_article_list()

        for i in range(1, sheet.nrows):
            row = sheet.row(i)
            info = dict((attributes[k], cell.value) for k, cell in enumerate(row))
            article = self.create_article_for_info(info)
            article_list.add_article(article, self.db_source())

        return article_list
