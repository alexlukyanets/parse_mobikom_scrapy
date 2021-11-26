from scrapy.exporters import CsvItemExporter

FIELDNAMES = ['name', 'href', 'grivna_price', 'dollar_price', 'instock',
              'image_href', 'description', 'images_href', 'date_parsed']


class ParseMobikomPipeline:
    def __init__(self):
        self.file = open('product_data.csv', 'wb')
        self.exporter = CsvItemExporter(self.file, encoding='utf-8',
                                        fields_to_export=FIELDNAMES)
        self.exporter.start_exporting()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item
