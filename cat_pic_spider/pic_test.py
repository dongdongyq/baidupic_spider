# -*- coding: utf-8 -*-
import requests
import time
import os
import random
import pymysql
import multiprocessing
import threading
from bs4 import BeautifulSoup

MYSQL_HOST = 'localhost'
MYSQL_DBNAME = 'spider'
MYSQL_USER = 'root'
MYSQL_PASSWD = ''


class Pic_Spider(object):
    """
    使用代理池无限制爬取西刺代理网站，并保存至文件
    """
    def __init__(self):
        self.table_name = 'banana'
        # 连接数据库
        self.connect = pymysql.connect(
            host=MYSQL_HOST,
            db=MYSQL_DBNAME,
            user=MYSQL_USER,
            passwd=MYSQL_PASSWD,
            charset='utf8',
            use_unicode=True)
        # 保存文件的路径
        self.path = os.path.join(os.path.abspath('..'), "data")
        print(self.path)
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        # 设置头信息
        self.headers = self.set_headers()
        # 代理池文件路径
        self.proxy_pool_path = r"D:\python_project\github_spider\proxy_spider2\data\available_http_proxy.txt"
        # 代理池列表
        self.proxy_pool = self.get_proxy_pool(self.proxy_pool_path)
        # 代理指针，-1表示不使用代理
        self.proxy_pool_index = 0
        self.proxy_flag = True
        self.proxy = {}

    def get_proxy_pool(self, path):
        """
        获取可用代理池文件里的代理ip
        :param path: 可用代理IP文件路径
        :return: 可用代理列表
        """
        proxy_pool = []
        with open(path, 'r', encoding='utf-8') as fp:
            for line in fp.readlines():
                proxy = line.strip()
                if proxy:
                    proxy_pool.append(proxy)
        return proxy_pool

    def set_headers(self):
        """
        设置请求头信息
        :return:请求头
        """
        USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36",
            "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)",
            "Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
            "Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
            "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
            "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
            "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
            "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/523.15 (KHTML, like Gecko, Safari/419.3) Arora/0.3 (Change: 287 c9dfb30)",
            "Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.6",
            "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.2pre) Gecko/20070215 K-Ninja/2.1.1",
            "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9) Gecko/20080705 Firefox/3.0 Kapiko/3.0",
        ]
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'referer': '',
        }
        return headers

    def get_url(self):
        search_sql = """select * from %s where is_download = FALSE""" % self.table_name
        cursor = self.connect.cursor()
        cursor.execute(search_sql)
        image_items = cursor.fetchall()
        # print(image_items)
        if image_items:
            # print(image_item)
            cursor.close()
            return image_items
        return None

    def get_page(self, url):
        """
        发起请求并返回页面，设置代理，若代理返回错误或异常，则换下个代理继续执行
        :param url: 要爬取得网站
        :return: 网页源码
        """
        self.headers['referer'] = url
        try:
            if self.proxy_flag:
                proxy = self.proxy
            else:
                proxy = {"http": random.choice(self.proxy_pool)}
            response = requests.get(url, headers=self.headers, proxies=proxy, timeout=3)
            if response.status_code == 200:
                self.proxy = proxy
                return response.content
            else:
                self.proxy_pool_index += 1
                print("返回错误：", response.status_code)
                # print("返回请求：", response.request)
                if self.proxy_pool_index > 2:
                    self.proxy_pool_index = 0
                    return None
                return self.get_page(url)
        except Exception as e:
            print("返回异常：", url)
            self.proxy_pool_index += 1
            if self.proxy_pool_index > 2:
                self.proxy_pool_index = 0
                return None
            return self.get_page(url)

    def save_pic(self, pic, pageNum, image_type):
        """
        保存http代理信息到本地文件
        :param pic:
        :return:
        """
        img_path = self.path + "/" + str(pageNum) + '.' + str(image_type)
        if not os.path.exists(img_path):
            with open(self.path + "/" + str(pageNum) + '.' + str(image_type), 'wb') as fp:
                fp.write(pic)
        else:
            print(img_path + '已存在！')

    def close(self):
        self.connect.close()

    def download(self, image_item):
        update_sql = """update %s set is_download = TRUE where image_id = %s""" % (self.table_name, '%s')
        url = image_item[3]
        pic = self.get_page(url)
        if pic:
            self.connect.ping(True)
            cursor = self.connect.cursor()
            cursor.execute(update_sql, image_item[0])
            self.save_pic(pic, image_item[1], image_item[4])
            self.connect.commit()
            cursor.close()
            print(image_item)
        else:
            self.proxy_flag = False
        # time.sleep(1)

    def main(self):
        thread = []
        image_items = self.get_url()
        for image_item in image_items:
            t = threading.Thread(target=self.download, args=(image_item,))
            thread.append(t)
        for t in thread:
            t.start()
        for t in thread:
            t.join()
        self.close()


if __name__ == '__main__':
    # root_url = "http://imgsrc.baidu.com/imgad/pic/item/4610b912c8fcc3ce866f87169845d688d43f2063.jpg"
    xx = Pic_Spider()
    xx.main()
