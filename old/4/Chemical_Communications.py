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

global downset
downset=set()

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

def check(temp_data):
    global downset
    if not( temp_data['title']!='' and temp_data['ee']!='' and temp_data['pages']!='' and temp_data['url']!='' and temp_data['year']>1800 and temp_data['year']<2019 and temp_data['authors']!=''):
        if temp_data['title'] not in downset:
            downset.add(temp_data['title'])
            print"check error!!!",temp_data['title'],temp_data['authors'],temp_data['url']
        
def fill(temp):
    basicroute="http://pubs.rsc.org/"   #do not forget!
    if not re.match(r'^https?:/{2}\w.+$', temp):
        if temp[0]=='/':
            temp=basicroute+temp
        else:
            temp=basicroute+'/'+temp
    return temp

def getPage(url):
    try:
        driver.get(url)
    except:
        pass
    locator = (By.CSS_SELECTOR, 'div.capsule__action--buttons')
    while True:
        try:
            WebDriverWait(driver, 20, 0.5).until(EC.presence_of_element_located(locator))
            return getPaper(driver.page_source.encode('utf-8'),url)
        except BaseException,e:
            print 'base',e,url
            time.sleep(2+random.random())

allowedgroup=['Highlight','Review','Communication','Essay','Correspondence','Feature Article',]
blacklist=['Cover Picture','Frontispiz','Frontispiece','Graphical Abstract','Corrigendum','Corrigenda','New','Author Profile','Editorial','Obituary','Book Review','Minireview','And Finally','Conference Report','Cover','Correction','Retraction','Profile','Expression of Concern']#,'Comment']



def getPaper(data,url):
    global blacklist
#    print url
    issues=BeautifulSoup(data,'lxml')
    urlnode=issues.select_one("div.tab-control div#tabissues div.tab-content div.article-nav div.article-nav__bar a[href]")
    if urlnode:
        url2=fill(urlnode['href'].strip())
        if url2==url:
#            print 'urlsame',url
            return url
    else:
        print 'url2 not found!',url
        return ''
    try:
        mis_pages=issues.select("span.paging--label")
        if mis_pages:
            print 'mispages:',mis_pages[0].text
        year=int(re.findall(re.compile(r"\d\d\d\d"),issues.select("div.article-nav > div.list-control h4")[0].text)[0])
        assert year<2019 and year>1800
        paper_details=list()

        for paper in issues.select("div.tab-content > div.capsule.capsule--article"):
            flag=0
            gtemp=paper.select("span.capsule__context")
            grouptitle="EmPTY title"
            if gtemp:
                glist=gtemp[0].stripped_strings
                if glist:
                    grouptitle=(''.join(glist)).strip()
                    if grouptitle[-1]=='s':
                        grouptitle=grouptitle[:-1]
                    for example in allowedgroup:
                        if grouptitle==example:
                            flag=1
                            break
                    for example in blacklist:
                        if grouptitle==example:
                            flag=-1
                            break
            if flag==0:
                print "Titleunlisted! ",grouptitle,' : ',url
                blacklist.append(grouptitle)
            elif flag==1:
                temp_data=dict()
                temp_data['title']=paper.select("h3.capsule__title")[0].text.strip()
                temp_data['ee']=fill(paper.select("a.capsule__action")[0]['href'].strip())
                temp_data['year']=year
                temp=paper.select("div.capsule__footer > div.text--small")[0].stripped_strings
                temp2=re.findall("(\d+)(\s*)-(\s*)(\d+)",''.join(temp))
                if len(temp2)==1:
                    temp_data['pages']=temp2[0][0]+'-'+temp2[0][3]
                elif len(temp2)==0:
                    tpage=re.findall("\d+",''.join(temp))
                    if tpage:
                        temp_data['pages']=tpage[-1].strip()
                    else:
                        print "pages! ",temp," findall: ",temp2
                        temp_data['pages']=""
                else:
                    print "pages! ",temp," findall: ",temp2
                    temp_data['pages']=""

                temp=paper.select("div.capsule__footer > div.capsule__action--buttons a.btn.btn--primary.btn--tiny")
                if len(temp)==1:
                    temp_data['url']=fill(temp[0]['href'])
                else:
                    print "url! ",temp,'url:',url,'title',temp_data['title']
                    temp_data['url']=''

                if paper.select("div.article__authors"):
                    temp_data['authors']=re.sub("[\r\n\t]","",paper.select("div.article__authors")[0].text.strip().replace(",((\s*),)*",";")).replace("  ","")
                else:
                    print "Authors! ",temp
                    temp_data['authors']=""

                check(temp_data)
                paper_details.append(temp_data)

        if len(paper_details):
            insert_mongo("Chemistry","chemical_communications",paper_details)
            if len(paper_details)<5:
                print "short:",len(paper_details)
        else:
            print "PAGE empty!"
    finally:
        return url2



if __name__ == "__main__":
    options = Options()
    options.add_argument('-headless')
    driver = Firefox(executable_path='geckodriver', firefox_options=options)
    limit=2
    driver.set_page_load_timeout(limit)  
    driver.set_script_timeout(limit)
    drop_mongo("Chemistry","chemical_communications")
    url="http://pubs.rsc.org/en/journals/journalissues/cc?_ga=2.201445330.2121483789.1516728316-237121058.1516728316#!issueid=cc054008&type=current&issnprint=1359-7345"
#    url="http://pubs.rsc.org//en/journals/journal/cc?issueid=cc052024&issnprint=1359-7345"
#    url="http://pubs.rsc.org//en/journals/journal/cc?issueid=cc047038&issnprint=1359-7345"
    while url:
        url=getPage(url)
    print "FINISHED"



