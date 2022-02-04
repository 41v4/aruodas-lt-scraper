# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from datetime import datetime
import os
import time

import undetected_chromedriver as uc
import yaml
from scrapy import signals
from scrapy.http import HtmlResponse
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By


class AruodasSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class AruodasDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class SeleniumMiddleware:
    def __init__(self):
        proxy_fp = "./proxy.yml"
        options = uc.ChromeOptions()
        options.headless = True
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        if os.path.exists(proxy_fp):
            with open(proxy_fp, "r") as f:
                proxy = yaml.safe_load(f)["proxy"]
            proxy_for_uc = "--proxy-server=socks5://" + proxy
            options.add_argument(proxy_for_uc)
        self.driver = uc.Chrome(options=options)

    def detect_recaptcha(self):
        recaptcha_elems = self.driver.find_elements(
            By.CSS_SELECTOR, "div button.g-recaptcha"
        )
        if recaptcha_elems:
            recaptcha_elems[0].click()
            time.sleep(2)

    def save_page_source(self, page_source, fn):
        page_source_main_dir = "./page_sources"

        if not os.path.exists(page_source_main_dir):
            os.mkdir(page_source_main_dir)

        current_datetime = datetime.now()
        crawling_session_dir = "_".join(
            [
                str(current_datetime.year),
                str(current_datetime.month),
                str(current_datetime.day),
            ]
        )

        crawling_session_dir_joined = os.path.join(
            page_source_main_dir, crawling_session_dir
        )

        if not os.path.exists(crawling_session_dir_joined):
            os.mkdir(crawling_session_dir_joined)

        saving_fp = os.path.join(page_source_main_dir, crawling_session_dir, fn)

        with open(saving_fp, "w") as f:
            f.write(page_source)

    def extract_object_id(self, url):
        kw_to_ignore = "/puslapis/"

        if kw_to_ignore not in url:
            split_by = "/"
            url_splitted = url.strip("/").split(split_by)
            last_part = url_splitted[-1]
            object_id = last_part.split("-")[-1]
            try:
                int(object_id)
                return object_id
            except ValueError:
                return None
        else:
            return None

    def process_request(self, request, spider):
        url = request.url
        self.driver.get(url)
        self.detect_recaptcha()
        self.driver.save_screenshot("selenium_middleware.png")  # used for debugging

        html = self.driver.page_source
        object_id = self.extract_object_id(url)

        if object_id:
            self.save_page_source(html, object_id)

        response = HtmlResponse(
            self.driver.current_url,
            body=html.encode("utf-8"),
            request=request,
            encoding="utf-8",
        )
        return response
