import urllib2
from bs4 import BeautifulSoup

url = "http://zai.diamond.jp/fx"
html = urllib2.urlopen(url)


soup = BeautifulSoup(html, "html.parser")

for element in soup:
    class_element = element.get("class").pop(0)
    if class_element == "hitsuji":
        print class_element
