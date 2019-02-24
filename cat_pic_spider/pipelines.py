# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import os
import scrapy
import copy
from scrapy.exceptions import DropItem
from scrapy.pipelines.images import ImagesPipeline
from . import settings
import pymysql
from twisted.enterprise import adbapi


class MysqlPipelineTwo(object):
    """
    数据保存到数据库，同步执行
    """
    def __init__(self):
        self.table_name = settings.pic_name['name']
        # 连接数据库
        self.connect = pymysql.connect(
            host=settings.MYSQL_HOST,
            db=settings.MYSQL_DBNAME,
            user=settings.MYSQL_USER,
            passwd=settings.MYSQL_PASSWD,
            charset='utf8',
            use_unicode=True)

        # 通过cursor执行增删查改
        self.cursor = self.connect.cursor()
        # 创建数据表
        self.create_table()

    def process_item(self, item, spider):
        """
        提取到的item首先进行数据库查重，若没找到则插入数据库
        """
        if self.do_not_rep(item):
            self.do_insert(item)
        return item

    def create_table(self):
        """
        创建数据表，表名为爬虫名
        :return:
        """
        create_sql = """CREATE TABLE if not exists %s (
                          image_id int not null AUTO_INCREMENT,
                          image_pageNum int not null ,
                          search_word varchar (20) not null ,
                          image_url varchar (200) null ,
                          image_type varchar (20) null ,
                          image_title varchar (100) null ,
                          image_width int null ,
                          image_height int null ,
                          image_URLHost varchar (100) null ,
                          is_download tinyint (1) not null ,
                          PRIMARY KEY (image_id)
                        ) ENGINE=MyISAM DEFAULT CHARSET=utf8;""" % self.table_name
        self.cursor.execute(create_sql)

    def do_insert(self, item):
        """
        item插入数据库操作
        :param item: 提取的信息
        :return:
        """
        insert_sql = """insert into %s (image_pageNum,search_word,image_url,image_type,
                                image_title,image_width,image_height,image_URLHost,is_download) 
                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            """ % (self.table_name, '%s','%s','%s','%s','%s','%s','%s','%s','%s')
        self.cursor.execute(insert_sql, (item['image_pageNum'], item['search_word'],
                                    item['image_url'], item['image_type'],
                                    item['image_title'], item['image_width'],
                                    item['image_height'], item['image_URLHost'], False))

    def do_delete(self):
        """
        删除表
        :return:
        """
        delete_sql = """delete from %s""" % self.table_name
        self.cursor.execute(delete_sql)

    def do_not_rep(self, item):
        """
        查询操作
        :param item:
        :return:
        """
        # 查重处理
        sql = """select * from %s where image_url = %s""" % (self.table_name, '%s')
        self.cursor.execute(sql, item['image_url'])
        # 是否有重复数据
        repetition = self.cursor.fetchone()
        # 重复
        if repetition:
            return False
        return True

    def handle_error(self, failure):
        """
        插入数据库回调函数
        :param failure: 错误信息
        :return:
        """
        if failure:
            # 打印错误信息
            print(failure)

    def close_spider(self, spider):
        """
        数据提交并关闭数据库连接
        :param spider:
        :return:
        """
        self.connect.commit()
        self.cursor.close()
        self.connect.close()


class MysqlPipeline(object):
    """
    数据如库，异步操作
    """
    def __init__(self, dbpool):
        # 表名
        self.table_name = settings.pic_name['name']
        self.dbpool = dbpool
        # self.do_delete()
        # 创建数据表
        self.create_table()

    @classmethod
    def from_settings(cls, settings):
        """
        数据库建立连接
        :param settings: 配置参数
        :return: 实例化参数
        """
        adbparams = dict(
            host=settings['MYSQL_HOST'],
            db=settings['MYSQL_DBNAME'],
            user=settings['MYSQL_USER'],
            password=settings['MYSQL_PASSWORD'],
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor  # 指定cursor类型
        )
        # 连接数据池ConnectionPool，使用pymysql或者Mysqldb连接
        dbpool = adbapi.ConnectionPool('pymysql', **adbparams)
        # 返回实例化参数
        return cls(dbpool)

    def process_item(self, item, spider):
        """
        使用twisted将MySQL插入变成异步执行。通过连接池执行具体的sql操作，返回一个对象
        因提取数据的速度很快，而数据保存到数据库的速度较慢，所以会出现重复提交
        为了避免重复提交可以降低item提交数据的速度或者将item拷贝，然后再对拷贝的数据入库
        """
        print(item)
        # 深拷贝
        item_copy = copy.deepcopy(item)
        if item_copy:
            # 指定操作语句和操作数据
            search_sql = """select * from %s where image_url = %s""" % (self.table_name, '%s')
            # runQuery(sql, *arg, **kw) 返回结果
            ret = self.dbpool.runQuery(search_sql, item_copy['image_url'])
            # 回调函数
            ret.addCallback(self._res, item_copy)
        return item

    def create_table(self):
        """
        创建表
        :return:
        """
        create_sql = """CREATE TABLE if not exists %s (
                          image_id int not null AUTO_INCREMENT,
                          image_pageNum int not null ,
                          search_word varchar (20) not null ,
                          image_url varchar (200) null ,
                          image_type varchar (20) null ,
                          image_title varchar (100) null ,
                          image_width int null ,
                          image_height int null ,
                          image_URLHost varchar (100) null ,
                          is_download tinyint (1) not null ,
                          PRIMARY KEY (image_id)
                        ) ENGINE=MyISAM DEFAULT CHARSET=utf8;""" % self.table_name
        # runOperation(sql, *arg, **kw) 返回None
        self.dbpool.runOperation(create_sql)

    def do_insert(self, cursor, item):
        """
        数据插入操作
        :param cursor:
        :param item:
        :return:
        """
        # 对数据库进行插入操作，并不需要commit，twisted会自动commit
        table_sql = """insert into %s""" % self.table_name
        # print(table_sql)
        insert_sql = table_sql + """(image_pageNum,search_word,image_url,image_type,
                        image_title,image_width,image_height,image_URLHost,is_download) 
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """
        # print(insert_sql)
        cursor.execute(insert_sql, (item['image_pageNum'], item['search_word'],
                                    item['image_url'], item['image_type'],
                                    item['image_title'], item['image_width'],
                                    item['image_height'], item['image_URLHost'], False))

    def do_delete(self):
        """
        删除表
        :return:
        """
        delete_sql = """drop table %s""" % self.table_name
        self.dbpool.runOperation(delete_sql)

    def handle_error(self, failure):
        """
        插入数据库回调函数
        :param failure: 错误信息
        :return:
        """
        if failure:
            # 打印错误信息
            print(failure)

    def _res(self, res, item):
        """
        查询回调函数
        :param res: 查询结果
        :param item: 查询的数据
        :return:
        """
        print(item, res)
        if not res:
            # print('------->', res)
            # 若不存在则插入到数据库
            query = self.dbpool.runInteraction(self.do_insert, item)
            # 添加异常处理
            query.addCallback(self.handle_error)  # 处理异常


class PicPipeline(ImagesPipeline):
    """
    图片下载，并保存到本地
    """
    # 获取配置文件中配置的图片存储路径
    IMAGES_STORE = settings.IMAGES_STORE

    def get_media_requests(self, item, info):
        url = item['image_url']
        yield scrapy.Request(url)

    def item_completed(self, results, item, info):
        # result是一个二元组列表，第一个参数为下载是否成功，第二个参数是详细信息。url，path等数据
        image_path = [result['path'] for exist, result in results if exist]
        if not image_path:
            print('图片下载失败')
            raise DropItem("Item contains no images")
        else:
            print('图片下载成功:' + image_path[0])
        return item