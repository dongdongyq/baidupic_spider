# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class CatPicSpiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    search_word = scrapy.Field()
    image_url = scrapy.Field()
    image_title = scrapy.Field()
    image_type = scrapy.Field()
    image_width = scrapy.Field()
    image_height = scrapy.Field()
    image_pageNum = scrapy.Field()
    image_URLHost = scrapy.Field()
