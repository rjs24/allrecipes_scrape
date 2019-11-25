# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class Recipe_item(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    recipe_name = scrapy.Field()
    num_serves = scrapy.Field()
    ingredients = scrapy.Field()
    method_steps = scrapy.Field()
