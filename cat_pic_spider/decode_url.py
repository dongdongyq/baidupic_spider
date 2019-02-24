import re


class DecodeUrl(object):

    def baidu_pic_url(url):
        res = ''
        c = ['_z2C$q', '_z&e3B', 'AzdH3F']
        d = {'w':'a', 'k':'b', 'v':'c', '1':'d', 'j':'e',
             'u':'f', '2':'g', 'i':'h', 't':'i', '3':'j',
             'h':'k', 's':'l', '4':'m', 'g':'n', '5':'o',
             'r':'p', 'q':'q', '6':'r', 'f':'s', 'p':'t',
             '7':'u', 'e':'v', 'o':'w', '8':'1', 'd':'2',
             'n':'3', '9':'4', 'c':'5', 'm':'6', '0':'7',
             'b':'8', 'l':'9', 'a':'0', '_z2C$q':':',
             '_z&e3B':'.', 'AzdH3F':'/'}
        if (url==None or 'http' in url):
            return url
        else:
            j = url
            for m in c:
                j = j.replace(m, d[m])
            for char in j:
                if re.match('^[a-w\d]+$', char):
                    char = d[char]
                res = res+char
            return res
