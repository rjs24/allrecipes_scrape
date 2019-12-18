# allrecipes_scrape
Extract recipes data from allrecipes.co.uk

This scraper utilises the python scrapy framework with a mongodb connection for writing to 
a mongodb collection. The Selenium toolset is also used, utilizing a headless browser to deal
with the javascript consent button upon entry to the site and retention of cookies.

