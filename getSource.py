#!/usr/bin/python
# -*- encoding:utf-8 -*-

"""
@author : kelvin
@file : getSource
@time : 2018/5/4 15:52
@description : 访问网页，获取源码HTML，及网页截图

"""
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import datetime
import shutil
import random
import re
import os
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')    # python3 中这样改默认编码


def request(url):
    """爬虫形式访问网页，这里没用上了"""
    html = None
    try:
        s = requests.Session()
        s.headers["user-agent"] = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36"
        response = s.get(url, timeout=15)
        response.encoding = 'utf-8'        # 这么做使得后面中文不会出现乱码，绝大部分网站用这种编码
        html = response.text
    except:
        pass
    return html


def selenium_request(url):
    """模拟浏览器访问网页，这里整合到saveSource函数里面去了"""
    try:
        browser = webdriver.PhantomJS()         # 不弹出浏览器，速度快，截图可以截整个页面的
        # browser = webdriver.Firefox()
        browser.set_window_size(1200, 900)      # 设置浏览器窗口大小，截图
        browser.get(url)
        time.sleep(2)
    except:
        browser = None
    return browser


def saveSource(url, file_name, idx_file, is_phish, target=None):
    """
    访问网页将网页的HTML和页面截图保存下来
    :param url: 网页的URL
    :param file_name: 要保存的文件夹名称
    :param idx_file: 索引文件名
    :param is_phish: 用于区分是否是钓鱼网页，存到不同文件夹里面
    :param target: 保存钓鱼网站的target，is_phish=True的时候需要传入
    :return:
    """
    # browser = webdriver.PhantomJS()         # 不弹出浏览器，速度快，截图可以截整个页面的
    try:
        browser = webdriver.Firefox()
        browser.set_window_size(1200, 900)  # 设置浏览器窗口大小，截图
        browser.get(url)
        time.sleep(2)
    except:
        # browser.close()
        browser = None

    if browser:
        try:
            html = browser.page_source
        except:
            # browser.close()
            return
        if is_phish:
            idx_line = "{}!!!{}!!!{}\n".format(url, "./sourceData/phishing/"+str(file_name), target)
            path = "./sourceData/phishing/"+str(file_name)
        else:
            idx_line = "{}!!!{}\n".format(url, "./sourceData/legitimate/" + str(file_name))
            path = "./sourceData/legitimate/" + str(file_name)
        if not os.path.exists(path):
            os.makedirs(path)            # 不存在则创建目录，这个语句连同父目录一起创建
        with open(path+"/sourceHtml.txt", 'w', encoding='utf-8') as h:   # 统一用utf-8，中文才不会乱码
            html = BeautifulSoup(html, 'lxml').prettify()
            # print(html)
            h.write(html)
        try:
            browser.save_screenshot(path+"/screenShot.png")
        except:
            # browser.close()
            shutil.rmtree(path)         # 删除该文件夹
            return
        # 存索引文件
        idx_path = "./sourceData/index"
        if not os.path.exists(idx_path):
            os.makedirs(idx_path)
        with open(idx_path+"/"+idx_file, 'a+', encoding='utf-8') as ix:
            ix.writelines(idx_line)
        browser.close()


class GetSource:
    def __init__(self, link_file, start, end, idx_file):
        """
        从给定的文件中读取钓鱼网页链接并访问，下载HTML和页面图片并存储
        :param link_file: 给定的文件，如果是钓鱼，则从Phishtank上下载的，每一行是一个钓鱼网站的信息，
        第二列是链接，最后一列是目标。如果是合法，则每一行是一条链接
        :param start: 想要开始的链接的行数（从1开始，对应CSV文件的2），这样是以防某种原因下载中断了，可以继续接着开始
        :param end: 结束的行
        :param idx_file: 存索引文件的文件名，最好按照钓鱼和合法命名
        """
        self.link_file = "./sourceData/"+link_file
        self.start = start
        self.end = end
        self.idx_file = idx_file

    def phish_main(self):
        with open(self.link_file, encoding='utf-8') as f:
            lines = f.readlines()
        dt = datetime.datetime.now()
        for index, one_line in enumerate(lines[self.start:self.end]):     # 给定文件第一行是标题信息，不能取
            # html = request(one_link.rstrip('\n'))
            t1 = time.clock()
            one_link = one_line.split(',')[1]
            one_target = one_line.split(',')[-1].rstrip('\n').strip('"')   # 莫名其妙两边多了引号
            saveSource(one_link, "P"+str(self.start+index), self.idx_file, True, one_target)
            print("phishing {} cost time: {} s".format(self.start+index, time.clock()-t1))
            if index % 100 == 0:
                print("this 100 pages cost time: {}".format(datetime.datetime.now()-dt))
                dt = datetime.datetime.now()

    def legi_main(self):
        with open(self.link_file, encoding='utf-8') as f:
            links = f.readlines()
        dt = datetime.datetime.now()
        for index, one_link in enumerate(links[self.start-1:self.end]):
            t1 = time.clock()
            saveSource(one_link.rstrip('\n'), "L"+str(self.start+index), self.idx_file, False)
            try:
                with open("./sourceData/legitimate/"+"L"+str(self.start+index)+"/sourceHtml.txt", encoding='utf-8') as f:
                    this_html = f.read()
            except:
                this_html = None
            if this_html:
                # 解析网页，随机选取5条该网页的链接，访问并存储
                soup = BeautifulSoup(this_html, 'lxml')
                all_links_tag = soup.find_all(href=re.compile('^http'))
                links = []
                for link_tag in all_links_tag:
                    links.append(link_tag.get('href'))
                sample_link = random.sample(links, 5)
                for l_idx, link in enumerate(sample_link):
                    saveSource(link, "L"+str(self.start+index)+'_'+str(l_idx+1), self.idx_file, False)
                print("legitimate {} cost time: {} s".format(self.start + index, time.clock() - t1))
                if index % 100 == 0:
                    print("this 100 pages cost time: {}".format(datetime.datetime.now() - dt))
                    dt = datetime.datetime.now()

# collect phishing data. From the first line of verified_online.csv, to the end of line 10.
# index file save in phish_idx.txt
# p = GetSource('verified_online.csv', 19820, 20000, 'phish_idx.txt')
# p.phish_main()

l = GetSource('alexa_links.txt', 1, 2, 'legi_idx.txt')
l.legi_main()


