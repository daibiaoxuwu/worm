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
global errorset
errorset=set()


def check(temp_data):
    global errorset
    if not( temp_data['title']!='' and temp_data['ee']!='' and temp_data['pages']!='' and temp_data['url']!='' and temp_data['year']>1800 and temp_data['year']<2019 and temp_data['authors']!=''):
        if temp_data['title'] not in errorset: 
            print"check error!!!",temp_data['title'],temp_data['url']
            errorset.add(temp_data['title'])
        
def fill(temp):
    basicroute="http://pubs.acs.org"   #do not forget!
    if not re.match(r'^https?:/{2}\w.+$', temp):
        if temp[0]=='/':
            temp=basicroute+temp
        else:
            temp=basicroute+'/'+temp
    return temp

def getPage(url):

    driver.get(url)
    while True:
        try:
            return getPaper(driver.page_source.encode('utf-8'))
        except IndexError,e:
            print e,url
            time.sleep(2+random.random())
        

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

def writeout(data):
    f=file("out.html","w")
    f.write(data)
    f.close()

def getPaper(data):
    soup=BeautifulSoup(data,'lxml')
    #writeout(soup.prettify().encode('utf-8'))

    year=int(re.findall(re.compile(r"\d\d\d\d"),soup.select("div#tocHead div#tocMenu div#date")[0].text)[0])
    assert year>1800 and year<2019

    section=soup.select("div.articleBox")
    paper_details=list()
    for paper in section:
        temp_data=dict()
        try:
            piece=paper.select("div.articleBoxMeta div.titleAndAuthor div.hlFld-Title div.art_title.linkable")[0]
        except IndexError,e:
            print e,'title not found!',url
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
        check(temp_data)
        paper_details.append(temp_data)
        

    if(len(paper_details)<2):
        print len(paper_details),url
    insert_mongo("Chemistry","journal_of_the_american_chemical_society",paper_details)
    piece=soup.select("span.next")
    if piece:
        return fill(piece[0].a['href'])
    else:
        return ""

if __name__ == '__main__':
    drop_mongo("Chemistry","journal_of_the_american_chemical_society")
    url="http://pubs.acs.org/toc/jacsat/1/1"
    urlend="http://pubs.acs.org/toc/jacsat/140/3"
    while url and url!=urlend:
        url=getPage(url)


