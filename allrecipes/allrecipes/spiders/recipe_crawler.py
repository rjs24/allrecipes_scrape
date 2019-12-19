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
import sys

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
        self.scrape_govern_flag = False
        self.options = Options()
        self.options.add_argument('-headless')
        self.browser = Firefox(options=self.options)
        self.wait_period = WebDriverWait(self.browser, timeout=15)
        time.sleep(5)

    def start_requests(self):
        # implement equivalent of a crawlspider in base spider with selenium
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        print("parse called: ", response.url)
        if "consent" in str(response.url):
            #handle the consent button
            while "consent" in response.url:
                self.scrape_govern_flag = True
                try:
                    print("IN WHILE")
                    self.browser.get(response.url)
                    self.wait_period.until(
                        expected.visibility_of_element_located(
                            (By.CSS_SELECTOR, '#consentButtonContainer > button'))).click()
                    time.sleep(3)
                    html = self.browser.page_source
                    all_elems = scrapy.Selector(text=html)
                    for cat_links in all_elems.xpath('//*[@id="hubsSimilar"]//div//div/*'):
                        new_url = ''.join(cat_links.xpath("@href").extract())
                        if new_url:
                            while self.scrape_govern_flag == False:
                                if self.scrape_govern_flag == False and len(new_url) > 33:
                                    for i in range(0, 60):
                                        sys.stdout.write(str(i)+' ')
                                        sys.stdout.flush()
                                        time.sleep(i)
                                        if self.scrape_govern_flag == True:
                                            break
                                        else:
                                            continue
                                else:
                                    yield scrapy.Request(url=new_url, cookies=self.browser.get_cookies(), callback=self.parse)
                                    self.scrape_govern_flag = False
                                    break
                            else:
                                continue
                    break
                except:
                    break
        else:
            html_ret = response.text
            all_elements = scrapy.Selector(text=html_ret)
            print("RESPONSE_URL:  ", response.url)

            if all_elements.xpath('//*[@id="pageContent"]//div[1]//div[1]//section[1]//h1/a'):
                new_url = ''.join(
                    all_elements.xpath('//*[@id="pageContent"]//div[1]//div[1]//section[1]//h1//a/@href').extract())
                if new_url:
                    cleaned_url = new_url.replace("javascript:void(0)","")
                    print("CATEGORY_URL:  ",cleaned_url)
                    yield scrapy.Request(url=cleaned_url, cookies=self.browser.get_cookies(), callback=self.parse, errback=self.error_handler)

            if all_elements.xpath('//*[@id="sectionTopRecipes"]//div//div/*'):
                for recipe_links in all_elements.xpath('//*[@id="sectionTopRecipes"]//div//div[1]/*'):
                    new_url = ''.join(recipe_links.xpath('@href').extract())
                    if new_url:
                        cleaned_url = new_url.replace("javascript:void(0)", "")
                        print("RECIPE_URL:  ", cleaned_url)
                        try:
                            recipe_query = self.recipe_collection.find({"url":cleaned_url})
                            if recipe_query.count() == 0:
                                yield scrapy.Request(url=cleaned_url, cookies=self.browser.get_cookies(), callback=self.parse, errback=self.error_handler)
                            else:
                                continue
                        except pymongo.errors.OperationFailure as OF:
                            print("DB OPERATION FAILURE")
                    else:
                        continue
                next_page_url = ''.join(all_elements.xpath('//*[@id="pageContent"]//div[1]//div[1]//div[3]//a[1]/@href').extract())
                if next_page_url:
                    cleaned_url = next_page_url.replace("javascript:void(0)","")
                    if cleaned_url != "":
                        yield scrapy.Request(url=cleaned_url, cookies=self.browser.get_cookies(), callback=self.parse)
                    else:
                        self.scrape_govern_flag = True

            if all_elements.xpath('//*[@id="pageContent"]//div[2]//div/div//div[1]//div//section[2]//h2'):
                ingredients_flag = all_elements.xpath('//*[@id="pageContent"]//div[2]//div/div//div[1]//div//section[2]//h2/text()').extract()
                if ingredients_flag == ['\r\n        Ingredients\r\n\r\n            ', '\r\n    ']:
                    item = Recipe_item()
                    html_xpaths_response = scrapy.Selector(response)

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

    def ingredient_processor(self, ingredients_2_process):
        #short function to process/split text extracted to quantity, ingredient and form.

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