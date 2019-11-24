# -*- coding: utf-8 -*-
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as expected
from selenium.webdriver.support.wait import WebDriverWait

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.selector import HtmlXPathSelector
import time,random

class RecipeCrawlerSpider(CrawlSpider):
    name = 'recipe_crawler'
    allowed_domains = ['allrecipes.co.uk/']
    start_urls = ['http://allrecipes.co.uk/recipes/']


    rules = (
        #follow category links on allrecipes.co.uk/recipes/
        #then all recipes within each sub-category
        Rule(LinkExtractor(allow=(), restrict_xpaths=('//*[@id="hubsSimilar"]//div//div[1]//a')),
             follow=True),
        Rule(LinkExtractor(allow=(), restrict_xpaths=('//*[@id="hubsRelated"]//div[1]//a')),
                follow=True),
        Rule(LinkExtractor(allow=(), restrict_xpaths=('//*[@id="pageContent"]//div[1]//div[1]//section[1]//h1//a')),
                follow=True),
        Rule(LinkExtractor(allow=(), restrict_xpaths=('//*[@id="sectionTopRecipes"]//div//div[2]//h3//a')),
             follow=True),
        Rule(LinkExtractor(allow=(), restrict_xpaths=('//*[@id="pageContent"]//div[1]//div[1]//div[3]//a[1]')),
             follow=True)
    )

    def __init__(self):
        CrawlSpider.__init__(self)
        self.options = Options()
        self.options.add_argument('-headless')
        self.browser = Firefox(options=self.options)
        self.wait_period = WebDriverWait(self.browser, timeout=15)
        self.browser.get("http://allrecipes.co.uk/consent/?dest=/recipes/")
        self.wait_period.until(expected.visibility_of_element_located((By.CSS_SELECTOR, '#consentButtonContainer > button'))).click()

    def __del__(self):
        self.browser.close()
        CrawlSpider.__del__(self)

    def parse_items(self, response):

        html_xpaths_response = HtmlXPathSelector(response)

        print(html_xpaths_response)
