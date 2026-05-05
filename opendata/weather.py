import requests, json

city = input("請輸入縣市：")
city = city.replace("台","臺")


url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization=rdec-key-123-45678-011121314&format=JSON&locationName="  + city
Data = requests.get(url)
#print(Data.text)

WeatherTitle = json.loads(Data.text)["records"]["datasetDescription"]
print(WeatherTitle)

Weather = json.loads(Data.text)["records"]["location"][0]["weatherElement"][0]["time"][0]["parameter"]["parameterName"]
Rain = json.loads(Data.text)["records"]["location"][0]["weatherElement"][1]["time"][0]["parameter"]["parameterName"]
print(city + "目前天氣預報")
print(Weather + "，降雨機率：" + Rain + "%")
