import requests
from bs4 import BeautifulSoup
url = "https://www.atmovies.com.tw/movie/next/"
Data = requests.get(url)
Data.encoding = "utf-8"
sp = BeautifulSoup(Data.text, "html.parser")
#result=sp.select("td a")
result=sp.select(".filmListAllX li")
print(result)
	
for item in result:
	#print(item.text)
	#print(item.get("href"))
	#print(item)
	#print(item.get("src"))
	print(item.find("img").get("alt"))

	print("https://www.atmovies.com.tw" + item.find("a").get("href"))
	print()
	
