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

#0 检查数据项:
global errorset
errorset=set()
def check(temp_data,url2):
    temp_data['authors']=re.sub(",((\s*),)*",";",re.sub("[\r\n\t]","",temp_data['authors'].strip()).replace("and",",")).replace("  ","")
    temp_data['pages']=temp_data['pages'].strip().replace("\u2013","-")
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
            insert_mongo("error","5",[temp_data])   #change!

def fill(temp):
    basicroute="http://pubs.rsc.org/"   #do not forget!
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
    time.sleep(2)
    options = Options()
    options.add_argument('-headless')
    driver = Firefox(executable_path='geckodriver', firefox_options=options)
    limit=2
    driver.set_page_load_timeout(limit)  
    driver.set_script_timeout(limit)
    try:
        driver.get(url)
    except:
        pass
    locator = (By.CSS_SELECTOR, 'div.capsule__action--buttons')
    while True:
        try:
            WebDriverWait(driver, 400, 0.5).until(EC.presence_of_element_located(locator))
            text=getPaper(driver.page_source.encode('utf-8'),url)
            driver.execute_script('window.stop()')
            driver.close() 
            return text
        except BaseException,e:
            driver.execute_script('window.stop()')
            driver.close()  
            time.sleep(10)
            driver = Firefox(executable_path='geckodriver', firefox_options=options)
            limit=2
            driver.set_page_load_timeout(limit)  
            driver.set_script_timeout(limit)
            driver.get(url)
            print 'base',type(e),url


allowedgroup=['Highlight','Review','Communication','Essay','Correspondence','Full Paper','Research Article','Article','Feature Article','Viewpoint','Focu','Paper']
blacklist=['Cover Picture','Frontispiz','Frontispiece','Graphical Abstract','Corrigendum','Corrigenda','New','Author Profile','Editorial','Obituary','Book Review','Minireview','And Finally',
           'Obritury','Dedication','Errata','Addendum','Instructions to Author','Masthead','Instructions for Author','Instructions for Author','Erratum','Content','Author Index','Subject Index']


def getPaper(data,url):
    global blacklist
    time.sleep(2)
#    print url
    issues=BeautifulSoup(data,'lxml')
    urlnode=issues.select_one("div.tab-control div#tabissues div.tab-content div.article-nav div.article-nav__bar a[href]")
    if urlnode:
        url2=fill(urlnode['href'].strip())
        if url2==url:
            return url
    else:
        return url
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
                print "GTNEW",grouptitle,url
                insert_mongo("error","5_GTNEW",[{'grouptitle':grouptitle,'link':url}])   #change!
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

                check(temp_data,url)
                paper_details.append(temp_data)

        if len(paper_details):
            insert_mongo("Chemistry","chemical_communications",paper_details)
        print len(paper_details),url
        if len(paper_details)<5:
            print 'SHORT!'
            
    finally:
        return url2



if __name__ == "__main__":
    
#    drop_mongo("Chemistry","chemical_communications")
#    url="http://pubs.rsc.org/en/journals/journalissues/cc?_ga=2.201445330.2121483789.1516728316-237121058.1516728316#!issueid=cc054008&type=current&issnprint=1359-7345"
    url="http://pubs.rsc.org//en/journals/journal/cc?issueid=cc006023&issnprint=1359-7345"
    urlend="http://pubs.rsc.org/en/journals/journalissues/cc#!issueid=cc1996_0_0&type=current&issnprint=1359-7345"
    while url and url!=urlend:
        url=getPage(url)
    print "FINISHED AT",url




