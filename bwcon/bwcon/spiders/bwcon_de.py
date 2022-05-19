import scrapy


class BwconDeSpider(scrapy.Spider):
    name = 'bwcon_de'
    allowed_domains = ['bwcon.de']
    start_urls = ['http://bwcon.de/']

    def parse(self, response):
        pass
