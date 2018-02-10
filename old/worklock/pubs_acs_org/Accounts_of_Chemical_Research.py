# -*- coding: utf-8 -*-
# plos3.py 使用selenium启动火狐爬取数据

import urllib
import urllib2
import re
import bs4
import pymongo
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import random
import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import pprint

driver = webdriver.Firefox()
        
#0 检查数据项:
global errorset
errorset=set()
def check(temp_data,url2):
    global errorset
    if not( temp_data['title']!='' and temp_data['ee']!='' and temp_data['pages']!='' and temp_data['url']!='' and temp_data['year']>1800 and temp_data['year']<2019 and temp_data['authors']!=''):
        if temp_data['title'] not in errorset: 
            string="checkerr:"+temp_data['title']+';'
            if temp_data['pages']=='':
                string=string+'PAGESNONE;'
            if temp_data['authors']=='':
                string=string+'AUTHORSNONE;'
            if temp_data['ee']=='':
                string=string+'EENONE;'
            if temp_data['url']=='':
                string=string+'URLNONE;'
            string=string+url2
            print string
            if temp_data['title'] != '':
                errorset.add(temp_data['title'])
            insert_mongo("error","1",[temp_data])   #change!

#填充url:
def fill(temp):
    basicroute="http://pubs.acs.org"   #与网页同步
    if not re.match(r'^https?:/{2}\w.+$', temp):
        if temp[0]=='/':
            temp=basicroute+temp
        else:
            temp=basicroute+'/'+temp
    return temp

def insert_mongo(dbname,tablename,data):
    client=pymongo.MongoClient('localhost',27017)
    db=client[dbname]
    posts=db[tablename]
    result = posts.insert_many(data)#important!insert_one or insert many
    client.close()

def drop_mongo(dbname,tablename):
    client=pymongo.MongoClient('localhost',27017)
    db=client[dbname]
    db[tablename].remove()
    client.close()
#抓取网页:使用完整的firefox:
def getPage(url):#看看有几个getpage避免死循环
    driver.get(url)
    while True:
        try:
            return getPaper(driver.page_source.encode('utf-8'),url)#参数数量
        except BaseException,e:
            print 'base',type(e),url   #输出
            time.sleep(random.random())
        

def getPaper(data,url):#参数数量
    soup=BeautifulSoup(data,'lxml')
    piece=soup.select("span.next")  #更改位置
    if piece:
        url2=fill(piece[0].a['href'])
        if url2==url:
            return url
    else:
        return url  #返回url

    year=int(re.findall(re.compile(r"\d\d\d\d"),soup.select("div#tocHead div#tocMenu div#date")[0].text)[0])
    assert year>1800 and year<2019

    section=soup.select("div.articleBox")
    paper_details=list()
    for paper in section:
        temp_data=dict()
        try:
            piece=paper.select("div.articleBoxMeta div.titleAndAuthor div.hlFld-Title div.art_title.linkable")[0]
        except IndexError,e:
            print 'TITIE ERROR: ',url#检查所有的err和print,尽量统一它们,加上url
            insert_mongo("error","1_TITLEERROR",[{'link':url}])   #change!
            continue
        temp_data['ee']=fill(piece.a['href'])
        temp_data['title']=piece.a.text.strip()
        if re.match("(Issue Publication Information$)|(Errata)|(Erratum)|(Subject Index$)|(Author Index$)|(Suggestions to Authors of)|(Masthead$)|(blank page$)|(Announcement$)|(To Appear in CHEMICAL REVIEWS,)|(In Color on the(.*?)Cover$)|(On the Cover$)|(Issue Editorial Masthead$)",temp_data['title']): 
            continue

        piece=paper.select("div.articleLinksIcons li.icon-item.pdf-low-res")
        if piece:
            temp_data['url']=fill(piece[0].a['href'])
        else:
            piece=paper.select("div.articleLinksIcons li.icon-item.pdf-high-res")
            if piece:
                temp_data['url']=fill(piece[0].a['href'])
            else:
                temp_data['url']=""

        temp_data['year']=year
        temp_data['pages']=""
        piece=paper.select("span.articlePageRange")
        if piece:
            piece=re.findall('\d+',piece[0].text)
            if len(piece)==2:
                if piece[0]==piece[1]:
                    temp_data['pages']=piece[0]
                else:
                    temp_data['pages']=piece[0]+'-'+piece[1]
            elif len(piece)==1:
                temp_data['pages']=piece[0]

        if paper.select("div.tocAuthors.afterTitle"):
            temp_data['authors']=re.sub("[\r\n\t]","",paper.select("div.tocAuthors.afterTitle")[0].text.strip().replace(",((\s*),)*",";")).replace("  ","")
        else:
            temp_data['authors']=""
        check(temp_data,url)#0 参数数量
        paper_details.append(temp_data)
        

    if(len(paper_details)<2):
        print len(paper_details),url#查看长度是否异常
    if len(paper_details):
        insert_mongo("Chemistry","accounts_of_chemical_research",paper_details)#插入数据库 注意名称
    return url2#返回url2

if __name__ == '__main__':
    drop_mongo("Chemistry","accounts_of_chemical_research")#删除数据库
    url="http://pubs.acs.org/toc/achre4/1/1"
    urlend="http://pubs.acs.org/toc/achre4/51/1"#设置urlend
    while url and url!=urlend:
        url=getPage(url)
    print "FINISHED AT",url#输出终止位置

#4 timeout我们把读秒由20改成了30
#5 以及grouptitle=example为适应大小写改成了re.match(example,grouptitle,re.I):
#6 在8上允许列表添加了'Full Paper','Research Article']
