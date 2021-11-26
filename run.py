from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

process = CrawlerProcess(get_project_settings())

from parse_mobikom.spiders.mobikom_biz_cralwer import MobikomBizCrawler

if __name__ == '__main__':
    scrapy_settings = Settings()
    scrapy_settings.setmodule('settings')
    runner = CrawlerProcess(settings=scrapy_settings)
    runner.crawl(MobikomBizCrawler)
    runner.start()
    runner.stop()
