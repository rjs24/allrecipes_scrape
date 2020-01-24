from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from allrecipes.spiders.recipe_crawler import RecipeCrawlerSpider

proc = CrawlerProcess(get_project_settings())
proc.crawl((RecipeCrawlerSpider))
proc.start()