# -*- coding: utf-8 -*-
import re
import urllib2
import pymongo
from pymongo import MongoClient
from pprint import pprint
import requests
import time
import random

client = MongoClient()
db = client.Chemistry
posts=db.Angewandte_Chemie
print "you are going to wipe a database. Are you sure?"
input()
db.Angewandte_Chemie.remove()
print posts.count()


reqpath='/doi/10.1002/anie.v57.4/issuetoc'
basicpath='http://onlinelibrary.wiley.com'

headers = {
        'Cookie': '__cfduid=d1e0cc7faadf90af5d64ff45aa2aba92c1503910637; cf_clearance=37fa4932d1e2dde34e9074b0f03aabb0d5f7e8ab-1503910642-31536000',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36'
}


#articleBox " doi="10.1021/ar50001a700"><div class="articleBoxMeta"><div class="titleAndAuthor"><div class="hlFld-Title"><h2><div class="art_title linkable"><a href="/doi/10.1021/ar50001a700">Masthead</a></div></h2></div><div class="tocAuthors afterTitle"><div class="articleEntryAuthor full"><span class="articleEntryAuthorsLinks"></span></div></div></div><div><span class="articlePageRange"></span></div><div class="coverdate"><strong>Publication Date: </strong>January 1968<span class="manType"> (<
#author
#<div class="tocAuthors afterTitle"><div class="articleEntryAuthor full"><span class="articleEntryAuthorsLinks"><span class="entryAuthor normal hlFld-ContribAuthor">William Summer Johnson</span></span></div></div>
#r1=re.compile("<div class=\"(.*?)Authors(.*?)</div>",re.S)






#title
#<div class="art_title linkable"><a href="/doi/10.1021/ar50001a001">Nonenzymic biogenetic-like olefinic cyclizations</a></div>
r0=re.compile("<div\ class=\"art_title\ linkable\"><a\ href=\"(.*?)\">(.*?)</a></div>")

#author
r1=re.compile("</a></div></h2></div><div class=\"tocAuthors afterTitle\"><div class=\"articleEntryAuthor full\"><span class=\"articleEntryAuthorsLinks\"><span class=\"entryAuthor normal hlFld-ContribAuthor\">(.*?)</span></span></div></div></div><div>",re.S)

#date
r2=re.compile("Publication Date: </strong>(.*?)(\d+?)<",re.S)


#pages
r3=re.compile("<span class=\"articlePageRange\">pp (\d+?)&ndash;(\d+?)</span>",re.S)
r4=re.compile(r"bottomViewLinks\">View: <a href=\"(.+?)\">PDF</a> \| <a href=\"(.+?)\">PDF w/ Links</a></div>",re.S)
#<div class="hlFld-Fulltext"><div class="bottomViewLinks">View: <a href="/doi/pdf/10.1021/ar50001a001">PDF</a> | <a href="/doi/pdfplus/10.1021/ar50001a001">PDF w/ Links</a></div><div class="SpotlightTeaserContainer"></div></div>
#/doi/pdf/10.1021/ar50001a001">PDF</a> | <a href="/doi/pdfplus/10.1021/ar50001a001
r5=re.compile("<a href=\"([^\"]*?)\">(\s*?)Next Issue",re.S)
while True:
    time.sleep(random.uniform(0.5,1))

    r = requests.get(basicpath+reqpath, headers=headers)
    r.encoding = 'utf'
    html=r.text
#    html=f.read()
    aa=html.find('articleBox')
    #rst1 = re.findall("<div class=\"articleBox(.*?)doi", html[aa+100:])
    rst1 = re.findall("articleBox(.*?)weo", html[aa+100:],re.S)
    #print html[aa:aa+10000]
    #pprint( re.findall("weo", html[aa+100:]) )
                                                                                                                                                                                    
    for i in rst1:
    #    print i

#title and ee
        temp = r0.search(i)
        if temp:
            n_title=temp.group(2)
            print n_title
            n_ee=temp.group(1)
            n_ee=basicpath+n_ee
            print n_ee
#url
            r = requests.get(n_ee, headers=headers)
            r.encoding = 'utf'
            html2=r.text
            aa=html2.find("bottomViewLinks")
            temp=r4.search(html2[aa:])
#            print html2[aa:aa+5000]
            if temp:
                n_url=basicpath+temp.group(2)
                print n_url
            else:
                print "url empty!----------------------------------------------------------"
                n_url=""
        else:
            print "title and ee empty!----------------------------------------------------------"
            n_title=""
            n_ee=""


#author
        n_author=r1.search(i)
        if n_author:
            n_author=re.sub("and",",",re.sub("<(.*?)>","",n_author.group(1)))
            print n_author
        else:
            print "author empty!-------------------------------------------"
            n_author=""
#year
        n_year=r2.search(i)
        if n_year:
            n_year=n_year.group(2)
            print n_year
        else:
            print "year empty!-------------------------------------------"
            n_year=""
#pages
        nn=r3.search(i)
        if nn:
            n_pages= nn.group(1) + "-" + nn.group(2)
            print n_pages
        else:
            print "pages empty!-------------------------------------------"
            n_pages=""
        print
        print

        if(re.search("<",n_title)) :
            print "title error!!!!!!!!!!!!!!!!!!!!!!"
            print n_title
            print
            input()

        if(re.search("<",n_url)) :
            print "url error!!!!!!!!!!!!!!!!!!!!!!"
            print n_url
            print
            input()
        if(re.search("<",n_author)) :
            print "author error!!!!!!!!!!!!!!!!!!!!!!"
            print n_author
            print
            input()
        if(re.search("<",n_ee)) :
            print "ee error!!!!!!!!!!!!!!!!!!!!!!"
            print n_ee
            print
            input()
        if(re.search("<",n_year)): 
            print "year error!!!!!!!!!!!!!!!!!!!!!!"
            print n_year
            print
            input()
        if(re.search("<",n_pages)): 
            print "pages error!!!!!!!!!!!!!!!!!!!!!!"
            print n_pages
            print
            input()

        post={"title":n_title,"url":n_url,"author":n_author,"ee":n_ee,"year":n_year,"pages":n_pages}
        posts.insert_one(post)


#nextissue
    nn=r5.search(html)
    if nn:
        print nn.group(0)
        reqpath= nn.group(1)
        print "nexturl======================================================="
        print reqpath
    else:
        print "nexturl empty!-------------------------------------------"
        print i
        break
'''

#    req2 = urllib2.Request(name3)
#    req2.add_header('User-agent', 'Mozilla 5.10')
#    res2 = urllib2.urlopen(req2)
#    html2 = res2.read()
#rst1 = re.findall("<li class=\"js-article-list-item\ article-item\ u-padding-top-xs\ u-margin-bottom-m\">(.*?)li>", html)
#rst1 = re.findall("<li class=\"js-article-list-item\ article(.*?)li>", html)
#for i in rst1:
#    f.write(i)
#    f.write('\n')
#f.close()

'''
