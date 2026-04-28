import requests
from bs4 import BeautifulSoup

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore



# 判斷是在 Vercel 還是本地
if os.path.exists('serviceAccountKey.json'):
    # 本地環境：讀取檔案
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    # 雲端環境：從環境變數讀取 JSON 字串
    firebase_config = os.getenv('FIREBASE_CONFIG')
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred)


import firebase_admin

from flask import Flask, render_template,request
from datetime import datetime
import random
app = Flask(__name__)

@app.route("/")
def index():
    link = "<h1>歡迎進入郭澔澄的網站首頁2</h1>"
    link += "<a href=/mis>課程</a><hr>"
    link += "<a href=/today>今天日期</a><hr>"
    link += "<a href=/about>關於澔澄</a><hr>"
    link += "<a href=/welcome?u=Howard&dep=資管A班>歡迎光臨</a><hr>"
    link += "<a href=/account>帳號密碼</a><hr>"
    link += "<a href=/math>數學計算</a><hr>"
    link += "<a href=/cup>擲杯</a><hr>"
    link += "<a href=/read>讀取Firestore資料(根據lab遞減排序，取前4筆)</a><br><hr>"
    link += "<a href=/search>作業老師辦公室查詢</a><br><hr>"
    link += "<a href=/sp1>爬蟲</a><hr>"
    link += "<a href=/movie>查詢即將上映電影</a><hr>"
    link += "<br><a href=/movie2>讀取開眼電影即將上映影片，寫入Firestore</a><hr><br>"
    link += "<br><a href=/movie3>輸入關鍵字,查詢相關電影資訊</a><hr><br>"
    return link
    return "歡迎進入郭澔澄的網站首頁2"

@app.route("/mis")
def course():
    return '<h1>資訊管理導論</h1><a href="/">回到網站</a>'

@app.route("/movie")
def movie():
    url = "https://www.atmovies.com.tw/movie/next/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        data = requests.get(url, headers=headers)
        data.encoding = "utf-8"
        sp = BeautifulSoup(data.text, "html.parser")
        
        # 根據開眼電影網結構抓取 li
        result = sp.select(".filmListAllX li")
        
        html_content = "<h1>即將上映電影</h1><ul>"
        
        for item in result:
            try:
                # 抓取電影名稱 (從 img 的 alt)
                name = item.find("img").get("alt")
                # 抓取超連結
                link = "https://www.atmovies.com.tw" + item.find("a").get("href")
                
                # 組合為 HTML 列表項目
                html_content += f'<li><a href="{link}" target="_blank">{name}</a></li>'
            except Exception:
                continue
        
        html_content += "</ul>"
        html_content += '<br><a href="/">回到首頁</a>'
        
        return html_content
    except Exception as e:
        return f"擷取資料失敗: {e}"
@app.route("/movie2")
def movie2():
    url = "http://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"

    sp = BeautifulSoup(Data.text, "html.parser")
    updateDate = sp.find("div",class_="smaller09 grey center").text.replace("更新時間：", "")

    result=sp.select(".filmListAllX li")
    info = ""
    for item in result:

      picture = item.find("img").get("src").replace(" ", "")
      title = item.find("div", class_="filmtitle").text

      movie_id = item.find("div", class_="filmtitle").find("a").get("href").replace("/", "").replace("movie", "")
      
      hyperlink = "http://www.atmovies.com.tw" + item.find("div", class_="filmtitle").find("a").get("href")
      show = item.find("div", class_="runtime").text.replace("上映日期：", "")
      if "片長" in show: 
        show = show.replace("片長：", "")
        show = show.replace("分", "")
        showDate = show[0:10]
        showLength = show[13:].replace(" ","")
      else:   
        showLength = "尚無片場資訊"
      info += movie_id + "\n" + picture + "\n" + title + "\n" + hyperlink + "\n" + showDate + "\n" + showLength + "\n\n"

      doc = {
          "title": title,
          "picture": picture,
          "hyperlink": hyperlink,
          "showDate": showDate,
          "showLength": showLength,
          "lastUpdate": updateDate
      }

      db = firestore.client()
      doc_ref = db.collection("電影2A").document(movie_id)
      doc_ref.set(doc)


    info += updateDate + "\n\n" 
 # 把最後一行的 lastUpdate 改成 updateDate
    return "近期上映電影已爬蟲及存檔完畢，網站最近更新日期為：" + updateDate



from flask import request

@app.route("/movie3")
def movie3():
    # 1. 取得網址參數 keyword，例如：/movie3?keyword=沙丘
    keyword = request.args.get("keyword")
    
    # 2. 如果使用者沒輸入關鍵字，回傳你想要的提示訊息（含超連結）
    if not keyword:
        return """
            <h2>電影關鍵字查詢</h2>
            <form action="/movie3" method="get">
                <input type="text" name="keyword" placeholder="請輸入電影名稱 (例如：沙丘)">
                <button type="submit">開始查詢</button>
            </form>
        """
    # 3. 連接 Firebase 抓取「電影2A」的資料
    db = firestore.client()
    movies_ref = db.collection("電影2A")
    docs = movies_ref.stream()

    info = f"<h3>關於『{keyword}』的查詢結果：</h3><hr>"
    found = False

    # 4. 跑迴圈找出符合關鍵字的電影
    for doc in docs:
        movie = doc.to_dict()
        title = movie.get("title", "")
        
        # 判斷標題是否包含關鍵字
        if keyword in title:
            found = True
            info += f"<b>電影名稱：</b>{title}<br>"
            info += f"<b>上映日期：</b>{movie.get('showDate', '暫無資料')}<br>"
            info += f"<b>片長：</b>{movie.get('showLength', '暫無資料')}<br>"
            info += f"<b>詳細介紹：</b><a href='{movie.get('hyperlink')}' target='_blank'>開眼電影網網址</a><br>"
            info += f"<img src='{movie.get('picture')}' width='200'><br><hr>"

    # 5. 如果整個資料庫都翻完了還是沒找到
    if not found:
        return f"抱歉，資料庫中找不到包含『{keyword}』的電影。"

    return info
@app.route("/sp1")
def sp1():
    R  = ""

    url = "https://howard-2026-a.vercel.app/about"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    #print(Data.text)
    sp = BeautifulSoup(Data.text, "html.parser")
    #result=sp.select("td a")
    result=sp.select("td a")
    print(result)
        
    for item in result:
        #print(item.text)
        #print(item.get("href"))
        #print(item)
        #print(item.get("src"))
        R += item.text + "<br>" + item.get("href") + "<br><br>"
    return R + "<br><a href='/'>回首頁</a>"
   
   

@app.route("/welcome",methods = ["GET"])
def welcome():
    
    x = request.values.get("u")
    y = request.values.get("dep")
    return render_template("welcome.html", name = x,dep = y)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        result = "您輸入的帳號是：" + user + "; 密碼為：" + pwd 
        
        return result
    else:
        return render_template("account.html")

@app.route("/math")
def math():
    return render_template("math.html")
@app.route('/cup', methods=["GET"])
def cup():
    # 檢查網址是否有 ?action=toss
    #action = request.args.get('action')
    action = request.values.get("action")
    result = None
    
    if action == 'toss':
        # 0 代表陽面，1 代表陰面
        x1 = random.randint(0, 1)
        x2 = random.randint(0, 1)
        
        # 判斷結果文字
        if x1 != x2:
            msg = "聖筊：表示神明允許、同意，或行事會順利。"
        elif x1 == 0:
            msg = "笑筊：表示神明一笑、不解，或者考慮中，行事狀況不明。"
        else:
            msg = "陰筊：表示神明否定、憤怒，或者不宜行事。"
            
        result = {
            "cup1": "/static/" + str(x1) + ".jpg",
            "cup2": "/static/" + str(x2) + ".jpg",
            "message": msg
        }
        
    return render_template('cup.html', result=result)

@app.route("/today")
def today():
    now = datetime.now()
    year = str(now.year)
    month = str(now.month)
    day = str(now.day)
    now = year +"年" + month +"月"+day +"日"
    return render_template("today.html", datetime = str(now))
@app.route("/about")
def about():
    return render_template("MIS2A.html")

@app.route("/read")
def read():
    # 這個路由維持原樣：只負責列出前 4 筆
    db = firestore.client()
    Temp = "<h3>前 4 筆老師資料：</h3>"
    collection_ref = db.collection("靜宜資管2026a")
    docs = collection_ref.order_by("lab", direction=firestore.Query.DESCENDING).limit(4).get()
    for doc in docs:
        Temp += str(doc.to_dict()) + "<br>"
    return Temp + "<br><a href='/'>回首頁</a>"

@app.route("/search", methods=["GET", "POST"])
def search():
    db = firestore.client()
    collection_ref = db.collection("靜宜資管2026a")
    
    # 修正重點 1：action 改成 "/search"，讓表單送回自己這個路由
    html_form = """
        <form method="GET" action="/search">
            <label>請輸入老師姓名關鍵字：</label>
            <input type="text" name="kw">
            <button type="submit">查詢</button>
        </form>
        <hr>
    """
    
    keyword = request.args.get("kw")
    result_text = ""
    
    if keyword:
        docs = collection_ref.get()
        found = False
        for doc in docs:
            user = doc.to_dict()
            name = user.get("name", "")
            lab = user.get("lab", "不詳")
            
            # 修正重點 2：搜尋邏輯
            if keyword in name:
                result_text += f"<h3>✅ 找到囉！{name} 老師研究室在：{lab}</h3>"
                found = True
        
        if not found:
            result_text = f"<p style='color:red;'>❌ 找不到包含「{keyword}」的老師。</p>"
    else:
        result_text = "<p>提示：請在上方輸入框輸入名字。</p>"
    
    return html_form + result_text + "<br><a href='/'>回首頁</a>"

if __name__ == "__main__":
    app.run(debug=True)

