#01.22.11.14 just started
#01.22.17.59 succeed catching the last part
import urllib
import urllib2
import requests
import re
import bs4

from bs4 import BeautifulSoup
from selenium import webdriver
import time
import random
import os
import pprint
def fill(temp):
    if not re.match(r'^https?:/{2}\w.+$', temp):
        if temp[0]=='/':
            temp="http://onlinelibrary.wiley.com"+temp
        else:
            temp="http://onlinelibrary.wiley.com/"+temp
    return temp

def getPage(url):
    headers = {
            'Cookie': '__cfduid=d1e0cc7faadf90af5d64ff45aa2aba92c1503910637; cf_clearance=37fa4932d1e2dde34e9074b0f03aabb0d5f7e8ab-1503910642-31536000',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36'
    }
    for i in range(10):
        try:
            r = requests.get(url, headers=headers)
            break
        except BaseException,e:
            print e
            time.sleep(2+random.random())
        
    r.encoding = 'utf'
    data=r.text#.encode("GB18030","ignore")
    #time.sleep(random.random())
    time.sleep(2+random.random())
    return data



allowedgroup=['Highlight','Review','Communication','Essay','Correspondence']
blacklist=['Cover Picture','Frontispiz','Frontispiece','Graphical Abstract','Corrigendum','Corrigenda','New','Author Profile','Editorial','Obituary','Book Review','Minireview','And Finally']

url="http://onlinelibrary.wiley.com/doi/10.1002/anie.v56.36/issuetoc"
while True:
    data=getPage(url)
    print url
    soup=BeautifulSoup(data,'lxml')
    if len(soup.select("h2.noMargin"))!=1:
        raise Exception("h2.noMargin"+str(len(soup.select("h2.noMargin")))+url)
    meta=soup.select("div#metaData")[0]
    year=int(re.findall(re.compile(r"\d\d\d\d"),meta.select("h2.noMargin")[0].text)[0])
    endpage=int(re.findall(re.compile(r"\d+"),meta.select("p.issuePage")[0].text)[1])
    url=fill(meta.select("a#previousLink")[0]['href'])


    paperlist=soup.select("li[id^='group']")
    paper_details=list()
    for group in paperlist:
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
        if flag==0:
            print("unlisted title! ",grouptitle,url)
            blacklist.append(grouptitle)
        elif flag==1:
            for paper in group.select("ol div.citation.tocArticle"):
                node=paper.a

                temp_data=dict()
                temp_data['ee']=fill(node['href'])

                m1=re.search(re.compile("^(.*?)(\([^\)]*?\))(\s*)$"),node.text)
                m2=m1.group(1).strip()
#                print m2
                pagestr=m1.group(2).strip()
                if m2[-1]==')':
                    m2=re.search(re.compile("^(.*?)(\([^\)]*?)\)$"),m2).group(1).strip()
                temp_data['title']=m2
                    
                startpage=re.search(re.compile("\d+"),pagestr).group(0)
                if startpage==pagestr:
                    temp_data['pages']=startpage+'-'
                else:
                    m3=re.findall("\d+",pagestr)
                    if len(m3)>2:
                        raise Exception("pages length is over 2:"+'-'.join(m3)+';'+url+'='+temp_data['title'])
                    elif len(m3)==1:
                        temp_data['pages']=m3[0]
                    else:
                        temp_data['pages']=m3[0]+'-'+m3[1]
                startpage=int(startpage)
  #              print startpage

                node=node.next_sibling
                if node.text.find('Version')==0:
                    temp_data['authors']=''
                else:
                    temp_data['authors']=re.sub("[\r\n\t]|and","",node.text.strip().replace(",",";")).replace("  ","")
                temp_data['year']=year
                if len(paper_details):
                    if paper_details[-1]['pages'][-1]=='-':
                        paper_details[-1]['pages']+=str(startpage-1)


                a10=paper.find("a",class_="readcubeEpdfLink",href=True)
                if a10==None:
                    raise Exception("in a0 find pdf failed!")
                soup2 = BeautifulSoup(getPage(fill(a10["href"])),'lxml')
                a15=soup2("noscript")
                for a16 in a15:
                    if a16.find("meta",content=re.compile("URL=")):
                        n_pdf=fill(re.search("URL=(.*)",a16.meta["content"]).group(1))
                        temp_data['url']=n_pdf
                    else:
                        print('pdf not found!')
                        temp_data['url']=''

                paper_details.append(temp_data)


    if len(paper_details):
        if paper_details[-1]['pages'][-1]=='-':
            paper_details[-1]['pages']+=str(endpage)
    if len(paper_details)<5:
        print "short:",len(paper_details)


