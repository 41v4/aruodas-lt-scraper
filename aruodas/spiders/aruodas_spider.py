from datetime import datetime

import scrapy
from aruodas.items import AruodasItem
from scrapy.http.request import Request
from scrapy.loader import ItemLoader


class AruodasSpiderSpider(scrapy.Spider):
    name = 'aruodas_spider'
    allowed_domains = ['aruodas.lt']
    start_urls = ['https://www.aruodas.lt/butai/vilniuje/']

    def parse(self, response):
        urls = response.css("tr.list-row td.list-adress a::attr(href)").getall()

        for url in urls:
            yield Request(url, callback=self.parse_item)

        pagination_elems = response.css("div.pagination a")
        for idx, elem in enumerate(pagination_elems):
            if elem.css(".active-page"):
                if idx < len(pagination_elems) - 1:
                    rel_next_page_url = pagination_elems[idx+1].css(".page-bt::attr(href)").get()
                    if rel_next_page_url:
                        next_page_url = response.urljoin(rel_next_page_url)
                        yield Request(next_page_url, callback=self.parse)
                break


    def parse_item(self, response):
        l = ItemLoader(item=AruodasItem(), selector=response)

        # add current datetime
        l.add_value("datetime", datetime.now())
        # add url
        l.add_value("url", response.request.url)
        # add street
        l.add_css("street", "div.obj-breadcrums div a span")
        # add header
        l.add_css("header", "h1.obj-header-text")
        # add images
        l.add_css("images", "div.obj-photos a.link-obj-thumb::attr(href)")
        # add price
        l.add_css("price", "div.price-block span.price-eur")
        # add price per sq m
        l.add_css("price_per_sq_m", "div.price-block span.price-per")

        # get property features
        for obj_details_elem in response.css("dl.obj-details"):
            dt_elems = obj_details_elem.css("dt")
            dd_elems = obj_details_elem.css("dd")
            obj_details_dict = {}
            for dt, dd in zip(dt_elems, dd_elems):
                if dd.css("::text").get().strip():
                    obj_details_dict[dt.css("::text").get().strip()] = dd.css("::text").get().strip()
                else:
                    obj_details_dict[dt.css("::text").get().strip()] = [i.strip() for i in dd.css("*::text").getall() if i.strip()]
        
        # add property features (after getting it and transforming to a dictionary)
        l.add_value("features", obj_details_dict)

        # add seller phone num
        l.add_css("seller_phone_num", "div.phone span")
        # add seller url
        l.add_css("seller_url", "div.obj-contacts div.long-link-wrapper a::attr(href)")
        
        # get property stats
        for obj_stats_elem in response.css("div.obj-stats"):
            dt_elems = obj_stats_elem.css("dt")
            dd_elems = obj_stats_elem.css("dd")
            obj_stats_dict = {}
            for dt, dd in zip(dt_elems, dd_elems):
                obj_stats_dict[dt.css("::text").get().strip()] = dd.css("::text").get().strip()
        # add property stats (after getting it and transforming to a dictionary)
        l.add_value("stats", obj_stats_dict)

        yield l.load_item()
