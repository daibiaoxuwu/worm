# -*- coding: utf-8 -*-
import re
import urllib2
import pymongo
from pymongo import MongoClient
from pprint import pprint
import requests
import time
import random

from bs4 import BeautifulSoup



#mongo
client = MongoClient()
db = client.Chemistry
posts=db.Angewandte_Chemie3001
print "you are going to wipe a database. Are you sure?"
input()
db.Angewandte_Chemie3001.remove()
print posts.count()
#paths
reqpath='/doi/10.1002/anie.v56.42/issuetoc'
basicpath='http://onlinelibrary.wiley.com'
headers = {
        'Cookie': '__cfduid=d1e0cc7faadf90af5d64ff45aa2aba92c1503910637; cf_clearance=37fa4932d1e2dde34e9074b0f03aabb0d5f7e8ab-1503910642-31536000',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36'
}


allowedgroup=['Highlights','Reviews','Communications','Essays','Correspondence']
blacklist=['Cover Pictures','Frontispiece','Graphical Abstract','Corrigendum','Corrigenda','News','Author Profiles','Author Profile','Editorial','Obituary','Book Reviews','Minireviews']
r0=re.compile('\(pages(\s+)(\d+)(.?)(\d+)(\s*)\)',re.S)
r1=re.compile('Version of Record online:(\s*)(\d+)(\s*)(...)(\s*)(\d\d\d\d)')

while True:
    time.sleep(random.uniform(2,3))
    print "startget!"
    r = requests.get((basicpath+reqpath), headers=headers)
    r.encoding = 'utf'
    html=r.text
    print "getword!"
#末尾有个break别忘了
#    f=file("in.html","r")
#    html=f.read()
    soup = BeautifulSoup(html,'lxml')

    number=0
    group=soup.find_all('li',id=re.compile('group(\d+?)'))
    for a0 in group:
        a1=a0.div.h3.string
        if a1==None:
            print("in <group\\d> find string failed!")
            print(a0.prettify())
            input()
        else:
            allowedgroupflag=0
            for b1 in allowedgroup:
                if a1==b1:
                    print "WORD:"+a1
                    print
                    allowedgroupflag=1
                    a2=a0.find("ol",class_="articles")
                    if a2==None:
                        print("in <group\\d> find <ol class=articles> failed!")
                        print(a0.prettify())
                        input()
                        break
                    print type(a2)
                    a33=a2.findall('li')
                    if a3==None:
                        print("in <ol class=articles> find <div class=\"citation tocArticle\" failed!")
                        print(a2.prettify())
                        input()
                        break
                    for a3 in a33:
#a3:each article
                        a4=a3.find("div",class_="citation tocArticle").find("a",href=True)
                        if a4==None:
                            print("in <div class=\"citation tocArticle\" find <a> failed!")
                            print(a2.prettify())
                            input()
                            break
                        a5=a4["href"]
                        if a5==None:
                            print("in <a> find href-word failed!")
                            print(a2.prettify())
                            input()
                        else:
                            n_ee=a5
                            print ("ee:"+n_ee)
                        a6=a4.stripped_strings
                        if a6==None:
                            print("in <a> find title and ee failed!")
                            print(a2.prettify())
                            input()
                        else:
                            n_title=""
                            for i in a6:
                                a7=r0.search(i)
                                if a7==None:
                                    n_title+=re.sub("\n+","",unicode(i))
                                else:
                                    n_pages=a7.group(2)+'-'+a7.group(4)
                                    print("pages:"+n_pages)
                                    break
                            if n_title=="":
                                print("title not found!")
                                print(a0.prettify())
                                input()
                            else:
                                print("title:"+n_title)
                        a8=a4.next_sibling
                        if a8.name<>'p':
                            print("author is not <p>: failed!")
                            print(a2.prettify())
                            input()
                        break
                        a9=a8.stripped_strings
                        if a9==None:
                            print("in <p> find author failed!")
                            print(a2.prettify())
                            input()
                        else:
                            n_author=""
                            for i in a9:
                                n_author+=re.sub("\n+","",unicode(i))
                            if n_author=="":
                                print("author not found!")
                                print(a2.prettify())
                                input()
                            else:
                                print ("author:"+n_author)
                                a11=a8.next_sibling
                                if a8.name<>'p':
                                    print("year is not <p>: failed!")
                                    print(a2.prettify())
                                    input()
                                    break
                                a12=a11.strings
                                if a12==None:
                                    print("in <p> find year failed!")
                                    print(a2.prettify())
                                    input()
                                    break
                                a14=""
                                for i in a12:
                                    a14+=i
                                a13=r1.search(a14)
                                if a13==None:
                                    print("in <p> find year failed!")
                                    print(a2.prettify())
                                    input()
                                    break
                                n_year=a13.group(6)
                                print('year:'+n_year)



                        a10=a0.find("a",class_="readcubeEpdfLink",href=True)
                        if a10==None:
                            print("in a0 find pdf failed!")
                            print(a2.prettify())
                            input()
                        n_pdf=basicpath+a10["href"]
                        #print n_pdf
                        time.sleep(random.uniform(3,5))
                        print "startget!"
                        r2 = requests.get(n_pdf, headers=headers)
                        r2.encoding = 'utf'
                        html2=r2.text
                        print "getword!"
#末尾有个break别忘了
#    f=file("in.html","r")
#    html=f.read()
                        soup2 = BeautifulSoup(html2,'lxml')
#                    a15=soup2.find("a",attrs={"ng-repeat":r"sup in ::supplements","target":r"_blank","ng-class":r"['supplement', sup.type]","ng-href":True,"ng-click":True,"class":["ng-scope","supplement","pdf"],"href":True,"style":""})
                        a15=soup2("noscript")
                        for a16 in a15:
                            if a16.find("meta",content=re.compile("URL=")):
                                n_pdf=basicpath+re.search("URL=(.*)",a16.meta["content"]).group(1)
                                
                                #<noscript>
                                 #  <meta content="0;URL=/doi/10.1002/anie.201709032/pdf" http-equiv="Refresh"/>
                                  #   </noscript>

                                print('pdf:'+n_pdf)
                            else:
                                print('pdf not found!')

                

                    n_title=n_title.strip()
                    n_url=n_url.strip()
                    n_author=n_author.strip()
                    n_ee=n_ee.strip()
                    n_year=int(n_year.strip())
                    n_pages=n_pages.strip()
                    post={"title":n_title,"url":n_url,"authors":n_author,"ee":n_ee,"year":n_year,"pages":n_pages}
                    posts.insert_one(post)
                    print posts.count()
                  
                    break
            if allowedgroupflag==0:
                for b1 in blacklist:
                    if a1==b1:
                        allowedgroupflag=1
            if allowedgroupflag==0:
                print "misallowed:"
                print a1
                input()
                                




                
    a17=soup.find("a",id="previousLink", class_="previous",string='Previous Issue',href=True)
    if a17:
        reqpath=a17["href"]
        print("next page: "+reqpath)
        print
        print
    else:
        break
print("job finished")
input()
