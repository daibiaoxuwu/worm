#01.22.11.14 just started
#01.22.17.59 succeed catching the last part
import urllib
import urllib2
import requests
import re
import bs4
import pymongo
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import random
import os
import pprint

import threading
lu=threading.local()
headers = {
        'Cookie': '__cfduid=d1e0cc7faadf90af5d64ff45aa2aba92c1503910637; cf_clearance=37fa4932d1e2dde34e9074b0f03aabb0d5f7e8ab-1503910642-31536000',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36'
}

def fill(temp):
    lu.temp=temp
    if not re.match(r'^https?:/{2}\w.+$', temp):
        if temp[0]=='/':
            lu.temp="http://onlinelibrary.wiley.com"+temp
        else:
            lu.temp="http://onlinelibrary.wiley.com/"+temp
    return lu.temp

def getPage(url):
    for lu.i in range(10):
        try:
            lu.r = requests.get(url, headers=headers)
            break
        except BaseException,lu.e:
            print lu.e
            time.sleep(5+3*random.random())
        
    lu.r.encoding = 'utf'
    lu.data=lu.r.text#.encode("GB18030","ignore")
    #time.sleep(random.random())
    time.sleep(random.random())
    return lu.data


def insert_mongo(dbname,tablename,data):    #data shared!
    client=pymongo.MongoClient('localhost',27017)
    db=client[dbname]
    posts=db[tablename]
    result = posts.insert_one(data)
    client.close()
def drop_mongo(dbname,tablename):
    client=pymongo.MongoClient('localhost',27017)
    db=client[dbname]
    db[tablename].remove()
    client.close()

allowedgroup=['Highlight','Review','Communication','Essay','Correspondence']
blacklist=['Cover Picture','Frontispiz','Frontispiece','Graphical Abstract','Corrigendum','Corrigenda','New','Author Profile','Editorial','Obituary','Book Review','Minireview','And Finally']


def getThread(_url,_url2):
    lu.url=_url
    while lu.url!=_url2:
        lu.data=getPage(lu.url)
        print lu.url
        lu.soup=BeautifulSoup(lu.data,'lxml')
        if len(lu.soup.select("h2.noMargin"))!=1:
            raise Exception("h2.noMargin"+str(len(lu.soup.select("h2.noMargin")))+lu.url)
        lu.meta=lu.soup.select("div#metaData")[0]
        lu.year=int(re.findall(re.compile(r"\d\d\d\d"),lu.meta.select("h2.noMargin")[0].text)[0])
        lu.endpage=int(re.findall(re.compile(r"\d+"),lu.meta.select("p.issuePage")[0].text)[1])
        lu.url=fill(lu.meta.select("a#previousLink")[0]['href'])


        lu.paperlist=lu.soup.select("li[id^='group']")
        lu.paper_details=list()
        for lu.group in lu.paperlist:
            lu.grouptitle=lu.group.h3.text.strip()
            if lu.grouptitle[-1]=='s':
                lu.grouptitle=lu.grouptitle[:-1]
            lu.flag=0
            for example in allowedgroup:
                if lu.grouptitle==example:
                    lu.flag=1
                    break
            for example in blacklist:
                if lu.grouptitle==example:
                    lu.flag=-1
                    break
            if lu.flag==0:
                print("unlisted title! ",lu.grouptitle,lu.url)
                blacklist.append(lu.grouptitle)
            elif lu.flag==1:
                for lu.paper in lu.group.select("ol div.citation.tocArticle"):
                    lu.node=lu.paper.a

                    lu.temp_data=dict()
                    lu.temp_data['ee']=fill(lu.node['href'])

                    lu.m1=re.search(re.compile("^(.*?)(\([^\)]*?\))(\s*)$"),lu.node.text)
                    lu.m2=lu.m1.group(1).strip()
                    lu.pagestr=lu.m1.group(2).strip()
                    if lu.m2[-1]==')':
                        lu.m2=re.search(re.compile("^(.*?)(\([^\)]*?)\)$"),lu.m2).group(1).strip()
                    lu.temp_data['title']=lu.m2
                        
                    lu.startpage=re.search(re.compile("\d+"),lu.pagestr).group(0)
                    if lu.startpage==lu.pagestr:
                        lu.temp_data['pages']=lu.startpage+'-'
                    else:
                        lu.m3=re.findall("\d+",lu.pagestr)
                        if len(lu.m3)>2:
                            raise Exception("pages length is over 2:"+'-'.join(lu.m3)+';'+lu.url+'='+lu.temp_data['title'])
                        elif len(lu.m3)==1:
                            lu.temp_data['pages']=lu.m3[0]
                        else:
                            lu.temp_data['pages']=lu.m3[0]+'-'+lu.m3[1]
                    lu.startpage=int(lu.startpage)

                    lu.node=lu.node.next_sibling
                    if lu.node.text.find('Version')==0:
                        lu.temp_data['authors']=''
                    else:
                        lu.temp_data['authors']=re.sub("[\r\n\t]|and","",lu.node.text.strip().replace(",",";")).replace("  ","")
                    lu.temp_data['year']=lu.year
                    if len(lu.paper_details):
                        if lu.paper_details[-1]['pages'][-1]=='-':
                            lu.paper_details[-1]['pages']+=str(lu.startpage-1)


                    lu.a10=lu.paper.find("a",class_="readcubeEpdfLink",href=True)
                    if lu.a10==None:
                        raise Exception("in a0 find pdf failed!")
                    lu.soup2 = BeautifulSoup(getPage(fill(lu.a10["href"])),'lxml')
                    lu.a15=lu.soup2("noscript")
                    for lu.a16 in lu.a15:
                        if lu.a16.find("meta",content=re.compile("URL=")):
                            lu.temp_data['url']=fill(re.search("URL=(.*)",lu.a16.meta["content"]).group(1))
                        else:
                            print('pdf not found!'.lu.url)
                            lu.temp_data['url']=''

                    lu.paper_details.append(lu.temp_data)


        if len(lu.paper_details):
            if lu.paper_details[-1]['pages'][-1]=='-':
                lu.paper_details[-1]['pages']+=str(lu.endpage)
            insert_mongo('Chemistry','Angewandte_Chemie',lu.paper_details)
        if len(lu.paper_details)<5:
            print "short:",len(lu.paper_details),lu.url
            f=file("1.html","w")
            f.write(lu.data)
            f.close

if __name__ == '__main__':
    drop_mongo('Chemistry','Angewandte_Chemie')
    urls=[
        "http://onlinelibrary.wiley.com/doi/10.1002/anie.v57.4/issuetoc",
        "http://onlinelibrary.wiley.com/doi/10.1002/anie.v48:47/issuetoc",
        "http://onlinelibrary.wiley.com/doi/10.1002/(SICI)1521-3773(19990115)38:1/2%3C%3E1.0.CO;2-G/issuetoc",
        "http://onlinelibrary.wiley.com/doi/10.1002/anie.v28:1/issuetoc",
        "http://onlinelibrary.wiley.com/doi/10.1002/anie.v18:1/issuetoc",
#        "http://onlinelibrary.wiley.com/doi/10.1002/anie.v8:12/issuetoc",
        "http://onlinelibrary.wiley.com/doi/10.1002/anie.v1:1/issuetoc"
        ]
    threadlist=[]
    for i in range(5):
        newthread=threading.Thread(target=getThread,args=(urls[i],urls[i+1]))
        threadlist.append(newthread)
        threadlist[-1].start()
        time.sleep(5+3*random.random())
        
    for i in threadlist:
        i.join()

