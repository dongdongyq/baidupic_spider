# -*- coding: utf-8 -*-
import scrapy
import json
import time
import urllib.parse
from ..settings import pic_name
from ..items import CatPicSpiderItem
from ..decode_url import DecodeUrl
from scrapy.exceptions import CloseSpider


class PicSpider(scrapy.Spider):
    name = pic_name['name']
    allowed_domains = ["baidu.com"]
    page = 0
    keyWord = pic_name['keyWord']
    params = {
        'tn': 'resultjson_com',
        'ipn': 'rj',
        'ct': '201326592',
        'is': '',
        'fp': 'result',
        'queryWord': '',
        'cl': '2',
        'lm': '-1',
        'ie': 'utf-8',
        'oe': 'utf-8',
        'adpicid': '',
        'st': '-1',
        'z': '',
        'ic': '0',
        'word': '',
        's': '',
        'se': '',
        'tab': '',
        'width': '',
        'height': '',
        'face': '0',
        'istype': '2',
        'qc': '',
        'nc': '1',
        'fr': '',
        'pn': '0',  # 翻页
        'rn': '30',
        'gsm': '1e',
        '1488942260214': ''
    }
    url = "https://image.baidu.com/search/acjson"

    def start_requests(self):
        self.params['word'] = self.keyWord
        self.params['queryWord'] = self.keyWord
        yield scrapy.FormRequest(self.url, method="GET", formdata=self.params)

    def parse(self, response):
        item = CatPicSpiderItem()
        response_json = response.text
        # 因返回的字符串包含一些奇怪的字符，不能反序列化，所以要替换掉
        response_json = response_json.replace(r'(д\')', '')
        # print(response_json)
        response_dict = json.loads(response_json)  # 转化为字典
        response_dict_data = response_dict['data']  # 图片的有效数据在data参数中
        # print(len(response_dict_data))
        if len(response_dict_data) == 1:
            print('结束')
            raise CloseSpider('数据爬取完毕！')
        for pic in response_dict_data:
            if pic:
                # print(pic)
                item['search_word'] = self.keyWord
                # 提取到的url需要解密
                item['image_url'] = DecodeUrl.baidu_pic_url(pic['objURL'])  # 百度图片搜索结果url
                item['image_type'] = pic['type']
                item['image_title'] = pic['fromPageTitleEnc']
                item['image_width'] = pic['width']
                item['image_height'] = pic['height']
                item['image_URLHost'] = pic['fromURLHost']
                item['image_pageNum'] = pic['pageNum']
                yield item
                # time.sleep(0.2)

        if self.page <= 10000:
            self.page += 1
            self.params['word'] = self.keyWord
            self.params['queryWord'] = self.keyWord
            self.params['pn'] = str(self.page*30)
            # 翻页
            yield scrapy.FormRequest(self.url, callback=self.parse, method="GET", formdata=self.params)


