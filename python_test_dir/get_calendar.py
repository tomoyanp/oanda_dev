# coding: utf-8
import urllib2
from bs4 import BeautifulSoup
import re
from datetime import datetime

#url = "http://zai.diamond.jp/fx"
url = "http://127.0.0.1:5000/"
html = urllib2.urlopen(url)

soup = BeautifulSoup(html, "html.parser")
class_element = soup.find_all("div")
#td_element = soup.find_all("tr")
td_element = soup.find_all("table")
#print td_element

#print td_element[2]
tr_element = td_element[2].find_all("tr")
tr_list = []
for elem in tr_element:
#    print "################"
#    print elem
    td_element = elem.find_all("td")
    for tdelem in td_element:
#        print tdelem
        try:
            span_elem = tdelem.find_all("img")
            tr_list.append
            #print span_elem
            for el in span_elem:
                src = el.get("src")
                if re.search("england.gif", src) or re.search("usa.gif", src) or re.search("euro.gif", src):
#                    print elem
                    tr_list.append(elem)
        except:
            pass



lst_index = []
for lst in tr_list:
    img_tag = lst.find_all("td")[0].find_all("img")
    if len(img_tag) > 0:
        lst_index.append(False)
    else:
        lst_index.append(True)
 

for (lst, index) in zip(tr_list, lst_index):
    try:
        if index:
            timing = lst.find_all("td")[0].string     
            print timing
            timing = datetime.strptime("2018-04-17 %s:00" % str(timing), "%Y-%m-%d %H:%M:%S")
            print timing
    except:
        pass

