# baidupic_spider
# 百度图片下载
爬虫介绍  
>1）爬取任意百度图片，通过修改settings.py里的pic_name  
>>如：pic_name = {'name': 'cat', 'keyWord': '猫'}  
>>注：name不能重复  
>2）可以下载图片到本地，也可以保存图片信息到数据库  
>>下载到本地使用scrapy提供的ImagesPipelines类，编写自己的类PicPipeline  
>>保存到数据库有同步和异步两种方式，如：MysqlPipeline（异步），MysqlPipelineTwo（同步）  
>3）百度图片返回使用ajax，所以需要对返回值进行反序列化。并且其图片地址进行了加密处理，  
>>所以还需解密，解密代码在decode_url.py文件  
>4）在下载图片时，有本地ip不可用，需要添加代理，所以需要建立代理池，当代理不可用时更换代理。  
