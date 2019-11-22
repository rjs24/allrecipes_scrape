# -*- coding: utf-8 -*-
import scrapy


class RecipeCrawlerSpider(scrapy.Spider):
    name = 'recipe_crawler'
    allowed_domains = ['allrecipes.co.uk/recipe']
    start_urls = ['http://allrecipes.co.uk/recipe/']

    def parse(self, response):
        pass
