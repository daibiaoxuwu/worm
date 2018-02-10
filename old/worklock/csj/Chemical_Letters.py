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
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.wait import WebDriverWait

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
            insert_mongo("error","8",[temp_data])   #change!

def getPage(url):
    time.sleep(2+random.random())
    while True:
        try:
            driver.get(url)
            return driver.page_source.encode('utf-8')
        except BaseException,e:
            print 'base',type(e),url
            time.sleep(2+random.random())
        

def insert_mongo(dbname,tablename,data):
    client=pymongo.MongoClient('localhost',27017)
    db=client[dbname]#change_1
    posts=db[tablename]
    result = posts.insert_many(data)
    client.close()

def drop_mongo(dbname,tablename):
    client=pymongo.MongoClient('localhost',27017)
    db=client[dbname]
    db[tablename].remove()
    client.close()

def getIssue():
    data=getPage("http://www.journal.csj.jp/loi/cl")
    soup=BeautifulSoup(data,'lxml')
    issuelist=soup.select("a.opener")
    issuelist=issuelist[1:]
    issuelinks=list()
    for issue in issuelist:
        temp=issue['href']
        if not re.match(r'^https?:/{2}\w.+$', temp):
            if temp[0]=='/':
                temp="http://www.journal.csj.jp"+temp
            else:
                temp="http://www.journal.csj.jp/"+temp
        data2=getPage(temp)
        soup2=BeautifulSoup(data2,'lxml')
        is2=soup2.select("div.slider.opened")
        if is2:
            is3=is2[-1].select("li")
            if is3:
                for is4 in is3:
                    temp=is4.a['href']
                    if not re.match(r'^https?:/{2}\w.+$', temp):
                        if temp[0]=='/':
                            temp="http://www.journal.csj.jp"+temp
                        else:
                            temp="http://www.journal.csj.jp/"+temp
                    issuelinks.append(temp)
                    print temp
    return issuelinks#here!back!

def getPaper(url):
    year=int(re.findall('\d+',url)[0])
    if year<20:
        year=year+1925
    else:
        year=year+1927
#    url="http://www.journal.csj.jp/toc/bcsj/89/6"
    data=getPage(url)
    soup=BeautifulSoup(data,'lxml')

#    year=int(re.findall(re.compile(r"\d\d\d\d"),soup.select("main section h1")[0].text)[0])

    paperlist=soup.select("ol.atcl-items li article")
    paper_details=list()
    for paper in paperlist:
        temp_data=dict()
        temp_data['year']=year
        temp_data['pages']=re.sub("\D+","-",paper.select("span.atcl-pageno")[0].text.strip())
        temp=paper.h3.a['href']
        if not re.match(r'^https?:/{2}\w.+$', temp):
            if temp[0]=='/':
                temp="http://www.journal.csj.jp"+temp
            else:
                temp="http://www.journal.csj.jp/"+temp
        temp_data['ee']=temp
        temp_data['title']=paper.h3.a.text.strip()
        if paper.select("div.atcl-authors"):
            temp_data['authors']=re.sub("[\r\n\t]","",paper.select("div.atcl-authors")[0].text.strip().replace(",((\s*),)*",";")).replace("  ","")
        else:
            temp_data['authors']=""
        temp=paper.select("div.actl-links.clear span.full-pdf-link a")
        if temp:
            temp=temp[0]['href']
            if not re.match(r'^https?:/{2}\w.+$', temp):
                if temp[0]=='/':
                    temp="http://www.journal.csj.jp"+temp
                else:
                    temp="http://www.journal.csj.jp/"+temp
            temp_data['url']=temp
        else:
            temp_data['url']=''
        check(temp_data,url)
        paper_details.append(temp_data)

    if len(paper_details):
        insert_mongo("Chemistry","chemistry_letters",paper_details)
    if len(paper_details)<5:
        print len(paper_details),url

if __name__ == '__main__':
    options = Options()
    options.add_argument('-headless')
    driver = Firefox(executable_path='geckodriver', firefox_options=options)
    drop_mongo("Chemistry","chemistry_letters")
    issuelinks=getIssue()
    for ii in issuelinks:
        getPaper(ii)
    print "FINISHED LIST"
