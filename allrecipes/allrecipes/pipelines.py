# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo
from scrapy.conf import settings
from scrapy import log

class AllrecipesPipeline(object):

    def __init__(self):
        connection = pymongo.MongoClient(
            settings['MONGODB_URI'],
            settings['MONGODB_PORT']
        )
        db_connect = connection[settings['MONGODB_DB']]
        self.recipe_collection = db_connect['recipes']

    def process_item(self, item, spider):
        #insert dictionaries from spider into db

        try:
            self.recipe_collection.insert_one(dict(item))
        except pymongo.errors.WriteError as we:
            err_string = "Record %s not added to db due to %s" % (item['recipe_name'], we)
            print(err_string)
            log.msg("Record not added to db", level=log.DEBUG, spider=spider)


