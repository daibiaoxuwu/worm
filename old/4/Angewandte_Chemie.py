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
    basicroute="http://onlinelibrary.wiley.com"   #do not forget!
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
    locator = (By.CSS_SELECTOR, 'input#selectAllBottom')
    while True:
        try:
            WebDriverWait(driver, 20, 0.5).until(EC.presence_of_element_located(locator))
            return getPaper(driver.page_source.encode('utf-8'),url)
        except BaseException,e:
            print 'base',e,url
            time.sleep(2+random.random())

allowedgroup=['Highlight','Review','Communication','Essay','Correspondence']
blacklist=['Cover Picture','Frontispiz','Frontispiece','Graphical Abstract','Corrigendum','Corrigenda','New','Author Profile','Editorial','Obituary','Book Review','Minireview','And Finally']



def getPaper(data,url):
    soup=BeautifulSoup(data,'lxml')
#next issue:url2
    try:
        url2=fill(soup.select("a#previousLink")[0]['href'])
        if url2==url:
#            print 'urlsame',url
            return url
    except IndexError,e:
        print 'url2 not found!',url
        return url

#meta    
    if soup.select("h2.noMargin")==None:
        return url2
    meta=soup.select("div#metaData")[0]

#year
    year=int(re.findall(re.compile(r"\d\d\d\d"),meta.select("h2.noMargin")[0].text)[0])

#endpage
    endpage=int(re.findall(re.compile(r"\d+"),meta.select("p.issuePage")[0].text)[1])
    startpage=0

#mainlist
    paperlist=soup.select("li[id^='group']")
    paper_details=list()
    for group in paperlist:
        try:
            grouptitle=group.h3.text.strip()
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
            print 'err1',e,url
            flag=1

        if flag==0:
            print("unlisted title! ",grouptitle,url)
            blacklist.append(grouptitle)
        elif flag==1:
            for paper in group.select("ol div.citation.tocArticle"):
                node=paper.a

                temp_data=dict()
                temp_data['ee']=fill(node['href'])

                m1=re.search(re.compile("^(.*?)(\([^\)]*?\))(\s*)$"),node.text)
                try:
                    if m1:
#                        print 'm1:',m1.group(0)
                        m2=m1.group(1).strip()
#                        print 'm2:',m2
                        pagestr=m1.group(2).strip()
#                        if m2[-1]==')':
#                            m2=re.search(re.compile("^(.*?)(\([^\)]*?)\)$"),m2).group(1).strip()
                        temp_data['title']=m2

                        m3=re.findall("\d+",pagestr)
                        if len(m3)>2:
                            print("pages length is over 2:"+'-'.join(m3)+';'+url+'='+temp_data['title'])
                            if m3[0]==m3[1]:
                                temp_data['pages']=m3[0]
                            else:
                                temp_data['pages']=m3[0]+'-'+m3[1]
                        elif len(m3)==1:
                            #print "======================================================================="
                            #print url
                            #input()
                            #temp_data['pages']=m3[0]+'-'
                            temp_data['pages']=m3[0]
                            startpage=int(m3[0])
                        elif len(m3)==0:
                            print 'm3(last bracket) without page![bef this url]',m1,url
                            temp_data['pages']=''
                        else:
                            if m3[0]==m3[1]:
                                temp_data['pages']=m3[0]
                            else:
                                temp_data['pages']=m3[0]+'-'+m3[1]
                            startpage=int(m3[0])
                    else:
                        print 'm1 without page![bef this url]',m1,url
                        temp_data['title']=m1
                        temp_data['pages']=''
                except AttributeError,e:
                    print 'err2',e
                    temp_data['title']=m1
                    temp_data['pages']=''



                node=node.next_sibling
                if node==None or node.text.find('Version')==0:
                    temp_data['authors']=''
                else:
                    temp_data['authors']=re.sub("[\r\n\t]|and","",node.text.strip().replace(",",";")).replace("  ","")
                temp_data['year']=year
                if len(paper_details):
                    if paper_details[-1]['pages'][-1]=='-' and str(startpage-1)!=paper_details[-1]['pages'][:-1]:
                        paper_details[-1]['pages']+=str(startpage-1)


                a10=paper.find("a",class_="readcubePdfLink",href=True)
                if a10==None:
                    temp_data['url']=''
                else:
                    temp_data['url']=fill(a10['href'])

                check(temp_data)
                paper_details.append(temp_data)


    if len(paper_details):
        if paper_details[-1]['pages'][-1]=='-' and str(endpage)!=paper_details[-1]['pages'][:-1]:
            paper_details[-1]['pages']+=str(endpage)
        insert_mongo("Chemistry","angewandte_chemie",paper_details)

#    print len(paper_details), 'next:',url2
    return url2


if __name__ == "__main__":
    options = Options()
    options.add_argument('-headless')
    driver = Firefox(executable_path='geckodriver', firefox_options=options)
    limit=2
    driver.set_page_load_timeout(limit)  
    driver.set_script_timeout(limit)
    drop_mongo("Chemistry","angewandte_chemie")
    url="http://onlinelibrary.wiley.com/doi/10.1002/anie.v57.5/issuetoc"
    urlend="http://onlinelibrary.wiley.com/doi/10.1002/anie.v1:1/issuetoc"
    while url and url!=urlend:
        url=getPage(url)



