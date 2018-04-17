import urllib2
from bs4 import BeautifulSoup

url = "http://zai.diamond.jp/fx"
html = urllib2.urlopen(url)


soup = BeautifulSoup(html, "html.parser")

print soup
print "##########################################################"
for element in soup:
    print element
#    class_element = element.get("class").pop(0)
#    if class_element == "hitsuji":
#        print class_element
