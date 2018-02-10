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
from selenium.webdriver.common.keys import Keys
import pprint
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.wait import WebDriverWait


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

        
def fill(temp):
    basicroute="http://www.nrcresearchpress.com"   #do not forget!
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

def getPage(url):
    try:
        driver.get(url)
    except:
        pass

    locator = (By.CSS_SELECTOR, 'div.article-tools')
    while True:
        try:
            WebDriverWait(driver, 40, 0.5).until(EC.presence_of_element_located(locator))
            return getPaper(driver.page_source.encode('utf-8'),url)
        except IndexError,e:
            print 'base',type(e),url
            time.sleep(2+random.random())

allowedgroup=['Highlight','Review','Communication','Essay','Correspondence','Article']
blacklist=['Cover Picture','Frontispiz','Frontispiece','Graphical Abstract','Corrigendum','Corrigenda','New','Author Profile','Editorial','Obituary','Book Review','Minireview','And Finally']



def getPaper(data,url):
    soup=BeautifulSoup(data,'lxml')
#next issue:url2
    try:
        url2=fill(soup.select("a.red-link-right")[0]['href'])
        if url2==url:
            return url
    except IndexError,e:
        print 'url2 not found!',url
        return url

#meta    
    if soup.select("h2.noMargin")==None:
        print 'METAERROR',url
        return url2
    meta=soup.select("div.journal-details h4")[0]

#year
    year=int(re.findall(re.compile(r"\d\d\d\d"),meta.text)[0])

#mainlist
    flag2=1     #标记 0代表无分组 1代表有
    paperlist=soup.select("div.articleGroup")
    if paperlist==None:
        paperlist=soup.select("div.border-gray.clearfix.toc")
        flag2=0
    paper_details=list()
    for group in paperlist:
        if flag2==1:
            try:
                grouptitle=group.h2.text.strip()
                if grouptitle[-1]==':':
                    grouptitle=grouptitle[:-1]
                if grouptitle[-1]=='s':
                    grouptitle=grouptitle[:-1]
                flag=0
                for example in allowedgroup:
                    if grouptitle==example:
                        flag=1
                        break
                for example in blacklist:
                    if grouptitle==example:
                        flag=-1
                        break
            except AttributeError,e:
                print 'GPERROR',e,url
                flag=1
        else:
            flag=1

        if flag==0:
            print("unlisted title! ",grouptitle,url)
            insert_mongo("error","4_GTNEW",[{'grouptitle':grouptitle,'link':url}])   #change!
            blacklist.append(grouptitle)
        elif flag==1:
            for paper in group.select("div.item-details.clearfix"):
                temp_data=dict()
                node=paper.select("div.abstractAndAccess")
                if node==None:
                    node=paper.select("div.articleEntryTitle")

                temp_data['title']=paper.span.h3.div.text.strip()

                temp_data['ee']=fill(paper.a['href'])

                try:
                    temp_data['pages']=re.search(re.compile(":(\s*)((\d+)-(\d+)),"),node[0].text).group(2).strip()
                except AttributeError,e:
                    temp_data['pages']=''

                node=paper.select("span.hlFld-ContribAuthor")
                if node==None: 
                    temp_data['authors']=''
                else:
                    temp_data['authors']=re.sub("[\r\n\t]|and","",node[0].text.strip().replace(",",";")).replace("  ","")
                temp_data['year']=year
                
                a10=paper.select("ul.icon-list-horizontal.clearfix a")
                temp_data['url']=''
                for a11 in a10:
                    if a11.text.find("PDF Plus")!=-1:
                        temp_data['url']=fill(a11['href'])
                        break

                check(temp_data,url)
                paper_details.append(temp_data)


    if len(paper_details):
        insert_mongo("Chemistry","canadian_journal_of_chemistry",paper_details)
    print len(paper_details), 'next:',url2
    return url2


if __name__ == "__main__":
    options = Options()
    options.add_argument('-headless')
    driver = Firefox(executable_path='geckodriver', firefox_options=options)
    limit=2
    driver.set_page_load_timeout(limit)  
    driver.set_script_timeout(limit)
    drop_mongo("Chemistry","canadian_journal_of_chemistry")
    url="http://www.nrcresearchpress.com/toc/cjc/96/1"
    urlend="http://www.nrcresearchpress.com/toc/cjc/29/1"
    while url and url != urlend:
        url=getPage(url)
    print "FINISHED AT",url



