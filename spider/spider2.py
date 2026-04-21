import requests
from bs4 import BeautifulSoup
url = "https://howard-2026-a.vercel.app/about"
Data = requests.get(url)
Data.encoding = "utf-8"
#print(Data.text)
sp = BeautifulSoup(Data.text, "html.parser")
#result=sp.select("td a")
result=sp.select("a")
print(result)
	
for item in result:
	#print(item.text)
	#print(item.get("href"))
	#print(item)
	#print(item.get("src"))
	print(item)
	print()
	return '<h1>資訊管理導論</h1><a href="/">回到網站</a>'

