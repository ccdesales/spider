import logging
import math
import urllib.parse
import scrapy

from typing import Dict, Iterable, NoReturn
from scrapy.http.response.html import HtmlResponse
from scrapy.http.request import Request
from scrapy.selector.unified import SelectorList
from twisted.python.failure import Failure
from items import BwConArticle

BASE_DOMAIN = 'https://www.bwcon.de'
MIN_RECORDS = 10
PAGE_SIZE = 3


class BwconDeSpider(scrapy.Spider):
    name = 'bwcon_de'
    allowed_domains = ['bwcon.de']
    start_urls = ['https://www.bwcon.de/aus-dem-netzwerk/meldungen']

    def parse(self, response: HtmlResponse, **kwargs) -> Iterable[Request]:
        """
        Parse landing page to yield `Request` objects representing
        each of the articles linked from there.
        """
        for page_num in range(get_max_pages_to_process()):
            form_values = get_form_values(response, page_num=page_num)
            encoded_form_values = urllib.parse.urlencode(form_values)
            form_action = response.css('#formLoadMore').xpath('@action').get()

            url = f'{BASE_DOMAIN}{form_action}&no_cache=1'

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            }

            # Load additional result pages by emulating an AJAX call
            yield scrapy.Request(
                url,
                method='POST',
                callback=self.parse_entry_group,
                errback=self.error_callback,
                headers=headers,
                body=encoded_form_values,
            )

    def parse_entry_group(self, response: HtmlResponse) -> Iterable[Request]:
        """
        Parse a result page containing links to additional articles.
        """
        for row in response.css('.bwc-panel-content .row'):
            link = row.css('a.eventheading').xpath('@href').get()
            url = f'{BASE_DOMAIN}{link}'

            request = scrapy.Request(
                url,
                callback=self.parse_entry,
                errback=self.error_callback,
            )
            yield request

    def parse_entry(self, response: HtmlResponse) -> Iterable[BwConArticle]:
        """Parse an article page."""
        detail = response.css('.bwc-meldungen-detail')
        pub_date = get_tag_text(detail.css('.date'))
        title = get_tag_text(detail.css('h3'))
        description = get_tag_text(detail.css('p')[0])
        content = response.css('.bwc-meldungen-detail article').extract().pop()

        result = BwConArticle(
            pub_date=pub_date,
            title=title,
            description=description,
            content=content,
        )

        logging.debug(result)
        yield result

    @staticmethod
    def error_callback(failure: Failure) -> NoReturn:
        logging.error(repr(failure))


def get_form_values(response: HtmlResponse, page_num: int) -> Dict[str, str]:
    counter_field = 'tx_bwconlist_bwcon[clickCounter]'
    form_fields = [
        'tx_bwconlist_bwcon[__referrer][@extension]',
        'tx_bwconlist_bwcon[__referrer][@vendor]',
        'tx_bwconlist_bwcon[__referrer][@controller]',
        'tx_bwconlist_bwcon[__referrer][@action]',
        'tx_bwconlist_bwcon[__referrer][arguments]',
        'tx_bwconlist_bwcon[__referrer][@request]',
        'tx_bwconlist_bwcon[__trustedProperties]',
        'tx_bwconlist_bwcon[clickCounter]',
        'tx_bwconlist_bwcon[recordUid]',
    ]

    form_values = {}
    for field in form_fields:
        form_values[field] = (
            response.css(f'#formLoadMore input[name="{field}"]').xpath('@value').get()
        )

    form_values[counter_field] = page_num
    return form_values


def get_tag_text(selector: SelectorList) -> str:
    _selector = selector.xpath('text()').get()
    if _selector:
        return _selector.strip()
    return ''


def get_max_pages_to_process() -> int:
    return math.ceil(MIN_RECORDS / PAGE_SIZE)
