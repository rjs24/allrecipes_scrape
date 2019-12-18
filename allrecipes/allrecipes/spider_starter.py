from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from .spiders.recipe_crawler import RecipeCrawlerSpider

process = CrawlerProcess(get_project_settings())
process.crawl(RecipeCrawlerSpider)
process.start()

