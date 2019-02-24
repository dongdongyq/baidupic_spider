# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html
import os
import random
import json
from .settings import USER_AGENT
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.web.client import ResponseNeverReceived
from twisted.internet.error import TimeoutError, ConnectionRefusedError, ConnectError, TCPTimedOutError


class UserAgentMiddleware(object):
    """
    添加请求头
    """
    def process_request(self, request, spider):
        ua = random.choice(USER_AGENT)
        request.headers['User-Agent'] = ua
        if request.url.split(":")[0] == "http":
            referer = request.url
            request.headers['referer'] = referer


class DownloadMiddleware(object):
    def __init__(self):
        self.error_info = {}

    def process_response(self, request, response, spider):
        if response.status != 200:
            if request.url in self.error_info.keys():
                self.error_info[request.url] += 1
            else:
                self.error_info[request.url] = 1
            if self.error_info[request.url] >= 10:
                raise HttpError(response)
        else:
            if request.url in self.error_info.keys():
                del self.error_info[request.url]
        print(self.error_info)
        return response


class ProxyMiddleware(object):
    # 遇到这些类型的错误直接当做代理不可用处理掉, 不再传给retrymiddleware
    DONT_RETRY_ERRORS = (TCPTimedOutError, TimeoutError, ConnectionRefusedError, ResponseNeverReceived, ConnectError, ValueError)

    def __init__(self):
        # HTTPS代理文件地址
        self.https_path = r"D:\python_project\github_spider\proxy_spider2\data\https_proxy.txt"
        # HTTP代理文件地址
        self.http_path = r"D:\python_project\github_spider\proxy_spider2\data\http_proxy.txt"
        # 保存可用HTTPS代理文件地址
        self.https_valid_path = os.path.join(os.path.abspath('..'), "data\https_proxy.txt")
        # 保存可用HTTP代理文件地址
        self.http_valid_path = os.path.join(os.path.abspath('..'), "data\http_proxy.txt")
        # 代理阈值
        self.proxy_threshold = True
        # 初始时使用-1号代理(即无代理)
        self.http_index = -1
        # 使用http代理还是https代理
        self.use_type = ''
        # http代理ip列表长度
        self.start_len = 0
        self.end_len = 1000
        # 初始化http代理ip列表
        self.httplist = self.get_proxy_list(self.http_path)

    def get_proxy_list(self, proxy_path):
        iplist = []
        # 从文件读取初始代理
        if os.path.exists(proxy_path):
            with open(proxy_path, 'r', encoding='utf-8') as fp:
                for line in fp.readlines()[self.start_len:self.end_len]:
                    # print(line.strip())
                    if not line:
                        continue
                    iplist.append({'proxy': line.strip(),
                                    'valid': True,
                                    'count': 0})
        return iplist

    def next_valid_ip(self):
        """
        切换到下一个可用ip
        :return:
        """
        while True:
            if self.http_index >= len(self.httplist) - 1:
                self.proxy_threshold = False
                break
            self.http_index = self.http_index + 1
            if self.httplist[self.http_index]["valid"]:
                break

    def invalid_ip(self, index):
        """
        禁止index指向的ip，并切换到下一个可用ip
        :param index: ip指针
        :return:
        """
        if index == -1:
            self.next_valid_ip()
            return
        if self.httplist[index]["valid"]:
            self.httplist[index]["valid"] = False
            if index == self.http_index:
                self.next_valid_ip()

    def dump_valid_proxy(self, path, httplist):
        """
        保存代理列表中有效的代理到文件
        """
        with open(path, "w", encoding='utf-8') as fd:
            for p in httplist:
                if p["valid"] and p['count'] != 0:
                    # 只保存有效的代理
                    pjson = json.dumps(p, ensure_ascii=False)
                    fd.write(pjson+'\n')

    def set_proxy(self, request):
        """
        将request设置使用为当前的或下一个有效代理
        """
        proxy = self.httplist[self.http_index]
        if proxy["proxy"]:
            request.meta["proxy"] = proxy["proxy"]

    def process_request(self, request, spider):
        # print("--->", request.url)
        # 判断请求类型
        self.use_type = request.url.split(':')[0]
        if not self.proxy_threshold:
            self.dump_valid_proxy(self.http_path, self.httplist)
            self.start_len += self.end_len
            self.end_len += 1000
            self.httplist = self.get_proxy_list(self.http_path)
            self.http_index = -1
        if self.use_type == 'http':
            """
            将request设置为使用代理
            """
            if self.http_index != -1:
                self.set_proxy(request=request)
            request.meta["proxy_index"] = self.http_index

    def process_response(self, request, response, spider):
        if self.use_type == 'http':
            proxy_index = request.meta["proxy_index"]
            # 如果返回的response状态不是200，重新生成当前request对象
            if response.status != 200:
                # 禁止当前ip并切换ip
                print('该图片下载异常：'+request.url)
                if 'proxy' in request.meta.keys():
                    print('该ip不可用', request.meta['proxy'])
                else:
                    print('本地ip不可用')
                self.invalid_ip(proxy_index)
                self.set_proxy(request)
                new_request = request.copy()
                new_request.dont_filter = True
                return new_request
            else:
                if proxy_index != -1:
                    self.httplist[proxy_index]['count'] += 1
                return response
        return response

    def process_exception(self, request, exception, spider):
        """
        处理由于使用代理导致的连接异常
        """
        print(exception)
        print(exception.__class__)
        if self.use_type == 'http':
            # 只有当proxy_index>fixed_proxy-1时才进行比较, 这样能保证至少本地直连是存在的.
            if isinstance(exception, self.DONT_RETRY_ERRORS):
                print('该图片下载异常：' + request.url)
                print("该ip出现异常", request.meta['proxy'])
                self.invalid_ip(request.meta['proxy_index'])
                self.set_proxy(request)
                new_request = request.copy()
                new_request.dont_filter = True
                return new_request
