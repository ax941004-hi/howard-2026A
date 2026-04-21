import requests
from bs4 import BeautifulSoup
url = "https://howard-2026-a.vercel.app/about"
Data = requests.get(url)
Data.encoding = "utf-8"
#print(Data.text)
sp = BeautifulSoup(Data.text, "html.parser")
result=sp.select("#pic")
print(result)
	
for item in result:
	#print(item.text)
	#print(item.get("href"))
	#print(item)
	print(item.get("src"))
	print()

