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
            insert_mongo("error","7",[temp_data])   #change!

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
            print 'base',type(e),url
            time.sleep(random.random())

allowedgroup=['Highlight','Review','Communication','Essay','Correspondence','Full Paper','Research Article','Article']
blacklist=['Cover Picture','Frontispiz','Frontispiece','Graphical Abstract','Corrigendum','Corrigenda','New','Author Profile','Editorial','Obituary','Book Review','Minireview','And Finally',
           'Obritury','Dedication','Errata','Addendum','Instructions to Author','Masthead','Instructions for Author','Instructions for Author','Erratum','Content','Author Index','Subject Index']



def getPaper(data,url):
    soup=BeautifulSoup(data,'lxml')
#next issue:url2
    try:
        url2=fill(soup.select("a#previousLink")[0]['href'])
        if url2==url:
            return url
    except:
        return url

#meta    
    if soup.select("h2.noMargin")==None:
        print 'METAERROR',url
        return url2
    meta=soup.select("div#metaData")[0]

#year
    year=int(re.findall(re.compile(r"\d\d\d\d"),meta.select("h2.noMargin")[0].text)[0])

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
            print 'GTERROR',e,url
            flag=1

        if flag==0:
            print("GTNEW",grouptitle,url)
            insert_mongo("error","7_GTNEW",[{'grouptitle':grouptitle,'link':url}])   #change!
            blacklist.append(grouptitle)
        elif flag==1:
            for paper in group.select("ol div.citation.tocArticle"):
                node=paper.a

                temp_data=dict()
                temp_data['ee']=fill(node['href'])
                temp_data['year']=year

                m1=re.search(re.compile("^(.*?)(\([^\)]*?\))(\s*)$"),node.text)
                try:
                    if m1:
                        m2=m1.group(1).strip()
                        pagestr=m1.group(2).strip()
                        temp_data['title']=m2
#should be improvised
                        m3=re.findall("\d+",pagestr)
                        if len(m3)>2:
                            print("PAGENUM OVER2:"+'-'.join(m3)+';'+url+'='+temp_data['title'])
                            insert_mongo("error","7_PAGENUM_OVER2",[temp_data])   #change!
                            if m3[0]==m3[1]:
                                temp_data['pages']=m3[0]
                            else:
                                temp_data['pages']=m3[0]+'-'+m3[1]
                        elif len(m3)==1:
                            temp_data['pages']=m3[0]
                        elif len(m3)==0:
                            print 'PAGENUM ZERO:',node.text,url
                            temp_data['pages']=''
                        else:
                            if m3[0]==m3[1]:
                                temp_data['pages']=m3[0]
                            else:
                                temp_data['pages']=m3[0]+'-'+m3[1]
                    else:
                        print 'PAGENUM_ZERO:',node.text,url
                        temp_data['title']=node.text
                        temp_data['pages']=''
                except AttributeError,e:
                    temp_data['title']=node.text
                    temp_data['pages']=''



                node=node.next_sibling
                if node==None or node.text.find('Version')==0:
                    temp_data['authors']=''
                else:
                    temp_data['authors']=re.sub("[\r\n\t]|and","",node.text.strip().replace(",",";")).replace("  ","")
                a10=paper.find("a",class_="readcubePdfLink",href=True)
                if a10==None:
                    temp_data['url']=''
                else:
                    temp_data['url']=fill(a10['href'])
                check(temp_data,url)
                paper_details.append(temp_data)


    if len(paper_details):
        insert_mongo("Chemistry","chemistry_a_european_journal",paper_details)
    if len(paper_details)<5:
        print len(paper_details),url

    return url2


if __name__ == "__main__":
    options = Options()
    options.add_argument('-headless')
    driver = Firefox(executable_path='geckodriver', firefox_options=options)
    limit=2
    driver.set_page_load_timeout(limit)  
    driver.set_script_timeout(limit)
    drop_mongo("Chemistry","chemistry_a_european_journal")
    url="http://onlinelibrary.wiley.com/doi/10.1002/chem.v24.6/issuetoc"
    urlend="http://onlinelibrary.wiley.com/doi/10.1002/chem.v1:1/issuetoc"
    while url and url!=urlend:
        url=getPage(url)
    print "FINISHED AT",url
    



