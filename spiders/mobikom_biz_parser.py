from typing import Optional, Generator, List, Iterator
from dataclasses import dataclass, field
from datetime import datetime
import logging

import bs4

from parse_mobikom.spiders.item_fields_handler import ItemFieldsHandler

logger = logging.getLogger(__name__)


@dataclass
class Product:
    instock: Optional[bool] = None
    grivna_price: Optional[float] = None
    dollar_price: Optional[float] = None
    name: Optional[str] = None
    href: Optional[str] = None
    image_href: Optional[str] = None
    description: Optional[str] = None
    images_href: List[str] = field(default_factory=list)
    date_parsed: Optional[datetime] = None


@dataclass
class User:
    guid: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    orders: List[str] = field(default_factory=list)


class MobikomBizParser(ItemFieldsHandler):
    @staticmethod
    def instock_value():
        return 'в наличии'

    @classmethod
    def parse_profile_page_data(cls, response):
        profile_data_dict = cls.deserialize(response.body_as_unicode())
        if not profile_data_dict:
            logger.error('Profile data is not found')
            return
        user_data = profile_data_dict.get('User')
        if not user_data:
            logger.error('User data is not found')
            return
        parsed_user = User()
        parsed_user.guid = user_data.get('Guid')
        parsed_user.name = user_data.get('Name')
        parsed_user.email = user_data.get('Email')
        parsed_user.phone = user_data.get('Phone')
        parsed_user.city = user_data.get('City')
        parsed_user.orders.extend(profile_data_dict.get('Orders'))
        return parsed_user

    @classmethod
    def extract_name(cls, div_tag: bs4.Tag) -> Optional[str]:
        name_tag = div_tag.find('span', {'class': 'product-name'})
        if not name_tag:
            return
        clear_name = name_tag.text
        if not clear_name:
            return
        return cls.clear_string(clear_name)

    @classmethod
    def extact_href(cls, div_tag: bs4.Tag) -> Optional[str]:
        href_tag = div_tag.find('a', {'class': 'product-item-img'})
        if not href_tag:
            return
        return cls.clear_string(href_tag.get('href'))

    @classmethod
    def extract_dollar_price(cls, div_tag: bs4.Tag) -> Optional[float]:
        price_tag = div_tag.find('p', {'class': 'list-cost'})
        if not price_tag:
            return
        clear_price = price_tag.text
        if not clear_price:
            return
        splitted_price = cls.clear_string(price_tag.text).split()
        if not splitted_price:
            return
        price_list = [item for item in splitted_price if item.replace('.', '').isdigit()]
        if len(price_list) != 1:
            return
        return cls.convert_string_to_float(''.join(price_list))

    @classmethod
    def extract_instock(cls, div_tag: bs4.Tag) -> Optional[bool]:
        instock_tag = div_tag.find('span', {'class': 'instock'})
        if not instock_tag:
            return
        clear_instock = instock_tag.text
        if not clear_instock:
            return
        if cls.clear_string(clear_instock).lower() not in cls.instock_value():
            return
        return True

    @classmethod
    def extract_div_tags_json_data(cls, response, first_desc_str: str) -> Optional[List[bs4.Tag]]:
        json_data = cls.deserialize(response.body_as_unicode())
        html = json_data.get('html')
        if not html:
            return
        soup = bs4.BeautifulSoup(html, 'lxml')
        if not soup:
            return
        div_tags = soup.find_all('div', {'class': first_desc_str})
        if not div_tags:
            return
        return div_tags

    @classmethod
    def extract_div_tags(cls, response) -> Optional[List]:
        soup = bs4.BeautifulSoup(response.body_as_unicode(), 'lxml')
        div_tags_list = []
        first_tag_description = 'product-item func-product-list-item func-first'
        div_tags_first = soup.find_all('div', {'class': first_tag_description}) \
                         or cls.extract_div_tags_json_data(response, first_tag_description)
        if div_tags_first:
            div_tags_list.extend(div_tags_first)

        other_div_tags = 'product-item func-product-list-item'
        div_tags = soup.find_all('div', {'class': other_div_tags}) \
                   or cls.extract_div_tags_json_data(response, other_div_tags)
        if div_tags:
            div_tags_list.extend(div_tags)
        return div_tags_list

    @classmethod
    def parse_new_products(cls, response) -> Generator[Product, None, None]:
        for div_tag in cls.extract_div_tags(response):
            product = Product()
            product.name = cls.extract_name(div_tag)
            if not product.name:
                logger.info('Name tag is not found')
                continue

            product.href = cls.extact_href(div_tag)
            if not product.href:
                logger.info('Href tag is not found')
                continue

            product.dollar_price = cls.extract_dollar_price(div_tag)
            if not product.dollar_price:
                logger.info('Price tag is not found')
                continue

            product.instock = cls.extract_instock(div_tag)
            if not product.instock:
                logger.info('Instock tag is not found')
                continue
            yield product

    @classmethod
    def parse_page_numbers(cls, response) -> Optional[Iterator]:
        soup = bs4.BeautifulSoup(response.body_as_unicode(), 'lxml')
        div_tag = soup.find('div', {'class': 'pagination x'})
        if not div_tag:
            return
        a_tag = div_tag.find('a', {'data-page': 'right'})
        if not a_tag:
            return
        href_text = a_tag.get('href')
        if not href_text:
            return
        digits = ''.join([item for item in cls.clear_string(href_text) if item.isdigit()])
        if not digits:
            return
        return iter(range(2, int(digits) + 2))

    @classmethod
    def extract_description(cls, soup: bs4.BeautifulSoup) -> Optional[str]:
        div_tag = soup.find('div', {'id': 'product-item-description'})
        if not div_tag:
            return
        p_tags = div_tag.find_all('p', {'class': None})
        if not p_tags:
            return
        text_list = [cls.clear_string(p_tag.text) for p_tag in p_tags]
        if not text_list:
            return
        return '\n'.join(text_list)

    @classmethod
    def extract_images_href(cls, soup: bs4.Tag) -> Optional[List]:
        div_tag = soup.find('div', {'id': 'product-item-imgs'})
        if not div_tag:
            return
        a_tags = div_tag.find_all('a')
        if not a_tags:
            return
        images_href_list = [a_tag.get('href') for a_tag in a_tags if a_tag.get('href')]
        if not images_href_list:
            return
        return images_href_list

    @classmethod
    def parse_detail_product(cls, response, product: Product) -> Optional[Product]:
        soup = bs4.BeautifulSoup(response.body_as_unicode(), 'lxml')
        product.description = cls.extract_description(soup)
        if not product.description:
            logger.info('Description is not found')

        images_href_list = cls.extract_images_href(soup)
        if images_href_list:
            product.images_href = images_href_list
        if not images_href_list:
            logger.info('Images href is not found')
            return
        return product

    @classmethod
    def parse_grivna_price(cls, response) -> Optional[float]:
        soup = bs4.BeautifulSoup(response.body_as_unicode(), 'lxml')
        p_tag = soup.find('p', {'class': 'info-cost'})
        if not p_tag:
            logger.error('Error with extract grivna price. P_tag is not found')
            return
        splitted_price = cls.clear_string(p_tag.text).split()
        if not splitted_price:
            return
        price_list = [item for item in splitted_price if item.replace('.', '').isdigit()]
        if not price_list:
            return
        return cls.convert_string_to_float(''.join(price_list))
