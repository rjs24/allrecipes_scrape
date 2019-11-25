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

from items import Recipe_item

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
        self.wait_period.until(expected.visibility_of_element_located((By.CSS_SELECTOR,
                                                                       '#consentButtonContainer > button'))).click()

    def __del__(self):
        self.browser.close()
        CrawlSpider.__del__(self)

    def ingredient_processor(self, ingredients_2_process):
        #short function to process/split text extracted to quantity, ingredient and form.

        print(ingredients_2_process)
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

    def parse_items(self, response):

        item = Recipe_item()
        html_xpaths_response = HtmlXPathSelector(response)

        item['recipe_name'] = html_xpaths_response.select('//*[@id="pageContent"]//div[2]//div//div//div[1]//div//section[1]//div//div[2]//h1//span/text()').extract()
        item['num_serves'] = html_xpaths_response.select('//*[@id="pageContent"]//div[2]//div//div//div[1]//div//section[2]//h2//small//span/text()').extract()
        item['ingredients'] = []
        item['method_steps'] = []

        ingredients_html = html_xpaths_response.select('//*[@id="pageContent"]//div[2]//div//div//div[1]//div//section[2]//ul')

        for ingredient in ingredients_html:
            ingredient_2_process = ingredient.select('// *//li//span/text()').extract()
            processed_ingredient = self.ingredient_processor(ingredient_2_process)
            item['ingredients'].append(processed_ingredient)

        methods_html = html_xpaths_response.select('//*[@id="pageContent"]//div[2]//div//div//div[1]//div//section[3]//ol')

        for step_number, methods in enumerate(methods_html):
            method = methods.select("// *//li/text()").extract()
            item['method_steps'].append({"step_num": step_number, "step_text": method })

        yield item

