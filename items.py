import scrapy


class ParseMobikomItem(scrapy.Item):
    name = scrapy.Field()
    href = scrapy.Field()
    grivna_price = scrapy.Field()
    dollar_price = scrapy.Field()
    instock = scrapy.Field()
    image_href = scrapy.Field()
    description = scrapy.Field()
    images_href = scrapy.Field()
    date_parsed = scrapy.Field()
