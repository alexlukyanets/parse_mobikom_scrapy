from typing import Generator, Optional
from dotenv import load_dotenv
from datetime import datetime
import logging
import os

import scrapy

from .mobikom_biz_parser import MobikomBizParser, Product
from ..items import ParseMobikomItem

logger = logging.getLogger(__name__)

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)


class MobikomBizCrawler(scrapy.Spider):
    def __init__(self, *args, **kwargs):
        super(MobikomBizCrawler, self).__init__(*args, **kwargs)
        self.pages = None

    name = 'mobikom_biz'

    custom_settings = {
        'LOG_LEVEL': 'INFO',
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 0.01,
        'DUPEFILTER_DEBUG': True,
        'ROBOTSTXT_OBEY': False,
    }

    def _response_parser(self):
        return MobikomBizParser

    @staticmethod
    def domain_url() -> str:
        return 'http://mobikom.biz/'

    @staticmethod
    def login_url() -> str:
        return 'https://mobikom.biz/account/logindata'

    @staticmethod
    def profile_page_data_url() -> str:
        return 'https://mobikom.biz/account/getprofilepagedata'

    @classmethod
    def new_products_url(cls) -> str:
        return f'{cls.domain_url()}catalog?all=New'

    @classmethod
    def new_page_url(cls, page=1) -> str:
        return f'{cls.domain_url()}catalog?all=New&p={page}&morePage={page}'

    @staticmethod
    def login_formdata() -> dict:
        return {
            'userEmail': os.getenv('EMAIL'),
            'userPass': os.getenv('PASSWORD')
        }

    def create_next_page_requst(self) -> Optional[scrapy.Request]:
        if not self.pages:
            return
        page = next(self.pages, None)
        if not page:
            logger.info('Request to page is finished')
            return
        return scrapy.Request(
            url=self.new_page_url(page),
            callback=self.parse_new_products
        )

    def start_requests(self) -> Generator[scrapy.Request, None, None]:
        yield scrapy.Request(url=self.domain_url(),
                             callback=self.login)

    def login(self, response) -> Generator[scrapy.FormRequest, None, None]:
        yield scrapy.FormRequest(
            url=self.login_url(),
            formdata=self.login_formdata(),
            callback=self.parse_data
        )

    def parse_data(self, response) -> Generator[scrapy.Request, None, None]:
        yield scrapy.Request(url=self.profile_page_data_url(),
                             callback=self.parse_profile_page_data)

    def parse_profile_page_data(self, response) -> Generator[scrapy.Request, None, None]:
        # user_data = self._response_parser().parse_profile_page_data(response)
        yield scrapy.Request(
            url=self.new_page_url(),
            callback=self.parse_new_products
        )

    def parse_new_products(self, response) -> Generator[scrapy.Request, None, None]:
        if not self.pages:
            self.pages = self._response_parser().parse_page_numbers(response)
        if not self.pages:
            logger.error('One page found')

        for product in self._response_parser().parse_new_products(response):
            yield scrapy.Request(
                url=f'{self.domain_url()}{product.href}',
                callback=self.parse_detail_product,
                cb_kwargs={'product': product},
                dont_filter=True
            )
        next_page_req = self.create_next_page_requst()
        if not next_page_req:
            return
        yield next_page_req

    def parse_detail_product(self, response, product: Product) -> Generator[scrapy.Request, None, None]:
        detail_product = self._response_parser().parse_detail_product(response, product)
        if not detail_product:
            return
        yield scrapy.Request(
            url=f'{self.domain_url()}{product.href}',
            callback=self.parse_grivna_price,
            cb_kwargs={'product': detail_product},
            meta={'dont_merge_cookies': True},
            dont_filter=True
        )

    def parse_grivna_price(self, response, product: Product) -> scrapy.Item:
        product.grivna_price = self._response_parser().parse_grivna_price(response)
        product.date_parsed = datetime.now()
        yield ParseMobikomItem(product.__dict__)
