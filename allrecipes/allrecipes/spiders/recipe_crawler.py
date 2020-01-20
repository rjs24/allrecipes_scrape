# -*- coding: utf-8 -*-
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as expected
from selenium.webdriver.support.wait import WebDriverWait
from scrapy import Spider
import scrapy
from ..items import Recipe_item
import time
import pymongo
from scrapy.utils.project import get_project_settings
import random

class RecipeCrawlerSpider(scrapy.Spider):
    name = 'recipe_crawler'
    allowed_domains = ['allrecipes.co.uk']
    #start_urls = ["http://allrecipes.co.uk/recipes/"]
    start_urls = ['http://allrecipes.co.uk/consent/?dest=/recipes/']

    def __init__(self, *args, **kwargs):
        super(Spider, self).__init__(*args, **kwargs)
        self.settings = get_project_settings()
        self.connection = pymongo.MongoClient(self.settings.get("MONGODB_URI"))
        self.db_connect = self.connection[self.settings.get('MONGODB_DB')]
        self.recipe_collection = self.db_connect['recipes']
        time.sleep(5)
        self.url_retry_counter = 0
        self.cat_links_list = []
        self.cats_links_index = 0

    def random_sleep_generator(self):
        #quick easy function to generate random sleep when required just before requests
        print("NOW ASLEEP")
        rand_int = random.randint(3, 10)
        return time.sleep(rand_int)

    def start_requests(self):
        # implement equivalent of a crawlspider in base spider with selenium
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse, errback=self.error_handler)

    def parse(self, response):

        print("RESPONSE_URL:  %s, %s" % (response.url, response.status))
        # parse through html to find xpaths and take appropriate action
        html_ret = response.text
        html_els = scrapy.Selector(text=html_ret)
        if html_els.xpath('//*[@id="hubsSimilar"]//div//div/*') and len(self.cat_links_list) == 0 and response.url == "http://allrecipes.co.uk/recipes/?o_is=LV_BC":
            for cat_links in html_els.xpath('//*[@id="hubsSimilar"]//div//div/*'):
                category_url = ''.join(cat_links.xpath("@href").extract())
                print("CATEGORY_URL:  ", category_url)
                if category_url != '':
                    self.cat_links_list.append(category_url)
                elif len(self.cat_links_list) == 12:
                    kickoff_cat_url = self.cat_links_list[0]
                    self.cats_links_index += 1
                    yield scrapy.Request(url=kickoff_cat_url, callback=self.parse, errback=self.error_handler)
                    self.random_sleep_generator()
                else:
                    continue

        elif html_els.xpath('//*[@id="pageContent"]//div[1]//div[1]//section[1]//h1/a') and response.url != "http://allrecipes.co.uk/recipes/?o_is=LV_BC":
            recipe_cat_url = ''.join(html_els.xpath('//*[@id="pageContent"]//div[1]//div[1]//section[1]//h1/a/@href').extract())
            if 'page=2' in recipe_cat_url:
                print("RECIPE_CAT_URL: ", recipe_cat_url)
                yield scrapy.Request(url=recipe_cat_url, callback=self.parse, errback=self.error_handler)
                self.random_sleep_generator()
            else:
                print("non valid recipe_cat_url", recipe_cat_url)

        elif html_els.xpath('//*[@id="sectionTopRecipes"]//div//div/*') and str(response.url) != "http://allrecipes.co.uk/recipes/?o_is=LV_BC":
            for recipe_links in html_els.xpath('//*[@id="sectionTopRecipes"]//div//div[1]/*'):
                new_url = ''.join(recipe_links.xpath('@href').extract())
                if new_url:
                    recipe_url = new_url.replace("javascript:void(0)", "")
                    print("RECIPE_URL:  ", recipe_url)
                    try:
                        recipe_query = self.recipe_collection.find({"url": recipe_url})
                        if recipe_query.count() == 0:
                            yield scrapy.Request(url=recipe_url, callback=self.parse, errback=self.error_handler)
                            self.random_sleep_generator()
                        else:
                            continue
                    except pymongo.errors.OperationFailure as OF:
                        print("DB OPERATION FAILURE", OF)
                else:
                    continue

        elif html_els.xpath('//*[@id="pageContent"]//div[1]//div[1]//div[3]//a[1]/@href') and "page=" in str(response.url):
            next_page_url = ''.join(
            html_els.xpath('//*[@id="pageContent"]//div[1]//div[1]//div[3]//a[1]/@href').extract())
            cleaned_url = next_page_url.replace("javascript:void(0)", "")
            if cleaned_url != "":
                yield scrapy.Request(url=cleaned_url, callback=self.parse, errback=self.error_handler)
                self.random_sleep_generator()
            else:
                print("END OF PAGES FOR THIS CATEGORY")
                new_cat_url = self.cat_links_list[self.cats_links_index]
                self.cats_links_index += 1
                yield scrapy.Request(url=new_cat_url, callback=self.parse, errback=self.error_handler)
                self.random_sleep_generator()

        elif html_els.xpath('//*[@id="pageContent"]//div[2]//div/div//div[1]//div//section[2]//h2') and "page=" not in str(response.url):
            ingredients_flag = html_els.xpath(
                '//*[@id="pageContent"]//div[2]//div/div//div[1]//div//section[2]//h2/text()').extract()
            print("INGREDIENTS_FLAG: ",ingredients_flag)
            if "Ingredients" in ''.join(ingredients_flag):
                item = Recipe_item()
                html_xpaths_response = scrapy.Selector(response)
                item['url'] = response.url
                recipe_nme = ''.join(html_xpaths_response.xpath(
                    '//*[@id="pageContent"]//div[2]//div//div//div[1]//div//section[1]//div//div[2]//h1//span/text()').extract())
                item['recipe_name'] = recipe_nme.strip()
                item['num_serves'] = int(''.join(html_xpaths_response.xpath(
                    '//*[@id="pageContent"]//div[2]//div//div//div[1]//div//section[2]//h2//small//span/text()').extract()))
                item['ingredients'] = []
                item['method_steps'] = []

                ingredients_html = html_xpaths_response.xpath(
                    '//section[contains(@class, "recipeIngredients")]//ul//li//span/text()').getall()

                for ingredient in ingredients_html:
                    ingredient_2_process = ingredient
                    processed_ingredient = self.ingredient_processor(ingredient_2_process)
                    item['ingredients'].append(processed_ingredient)

                methods_html = html_xpaths_response.xpath(
                    '//section[contains(@class, "recipeDirections")]//ol//li//span/text()').getall()

                for step_number, methods in enumerate(methods_html):
                    method = methods
                    print("method:  ", method)
                    item['method_steps'].append({"step_num": step_number, "step_text": method})

                yield item
        else:
            while self.url_retry_counter < 5:
                print("IN RETRY LOOP")
                last_response_url_retry = response.url
                self.url_retry_counter += 1
                yield scrapy.Request(url=last_response_url_retry, callback=self.parse, errback=self.error_handler)
                self.random_sleep_generator()
            else:
                return None

    def ingredient_processor(self, ingredients_2_process):
        #short function to process/split text extracted to quantity, ingredient and form.
        print("ingredient processor called")
        quantity = ''
        units = ''
        ingredient = ''
        form = ''
        special_measure_list = ['teaspoon', 'tsp', 'tablespoon', 'tbsp', 'large', 'medium', 'small', 'cup', 'teaspoons',
                                'tablespoons','pint','pinch','drop','dessertspoon']
        ingredients_list = ingredients_2_process.split(' ')
        for n, ingredients in enumerate(ingredients_list):
            if n == 0:
                for i, characters in enumerate(ingredients_list[n]):
                    if characters.isdigit() == True or characters == '/':
                        quantity += characters
                        continue
                    elif characters.isdigit() == False and characters.isalpha() == True:
                        starts_alpha_index = ingredients_list[n].index(characters)
                        if len(ingredients_list[n][starts_alpha_index:]) <= 3:
                            units += characters
                            continue
                        else:
                            break
            elif n == 1 and ingredients in special_measure_list:
                units = ingredients
                continue
            elif n >= 1 and ingredients not in special_measure_list and ',' not in ingredients:
                ingredient += ingredients
                ingredient += ' '
                continue
            elif n >= 1 and ingredients not in special_measure_list and ',' in ingredients:
                ingredient += ingredients.replace(',', '')
                form += ' '.join(ingredients_list[n+1:])
                break
            else:
                ingredient = ingredients
                break

        return {'quantity': quantity, 'units': units, 'ingredient': ingredient, 'form': form}

    def error_handler(self, failure):
        #function to catch request errors
        print("ERROR_HANDLER CALLED:  ",failure)
