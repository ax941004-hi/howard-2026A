import requests
from bs4 import BeautifulSoup
import time
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, render_template, request, make_response, jsonify
from google import genai
from google.genai import types
from datetime import datetime
import hashlib

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

# ======== 補上這兩行！宣告全域的 db 變數 ========
from firebase_admin import firestore
db = firestore.client()

import firebase_admin

from flask import Flask, render_template,request
from datetime import datetime
import random

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from urllib.parse import urljoin

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
    link += "<a href=/movie2>讀取開眼電影即將上映影片，寫入Firestore</a><hr>"
    link += "<a href=/movie3>輸入關鍵字,查詢相關電影資訊</a><hr>"
    link += "<a href=/road>113交通事故</a><hr>"
    link += "<a href=/weather>天氣查詢</a><hr>"
    link += "<a href=/rate>本週新片進DB</a><hr>"
    link += "<a href=/demo>對話框</a><hr>"
    link += "<a href=/AI>Gemini</a><hr>"
    link += "<a href=/ask>ask</a><hr>"
    link += "<a href=/message>message</a><hr>"
    link += "<a href=/webhook2>news</a><hr>"
    

    return link
    return "歡迎進入郭澔澄的網站首頁2"

import json

@app.route("/webhook2", methods=["GET", "POST"])
def webhook2():
    # ==========================================================
    # 情況 A：LINE / Dialogflow 傳訊息進來 (POST) ➡️ 輪流拿未看過的新聞
    # ==========================================================
    if request.method == "POST":
        req = request.get_json(silent=True, force=True)
        query_text = req.get("queryResult", {}).get("queryText", "")
        
        target_cat = "AI科技" 
        query_lower = query_text.lower()
        
        if "3c" in query_lower: target_cat = "3C"
        elif "財經" in query_lower or "金融" in query_lower: target_cat = "財經"
        elif "旅遊" in query_lower or "玩" in query_lower: target_cat = "旅遊"
        elif "國際" in query_lower or "國外" in query_lower: target_cat = "國際"
        elif "ai" in query_lower or "科技" in query_lower: target_cat = "AI科技"
        else:
            for cat in ["3C", "財經", "旅遊", "國際", "AI科技"]:
                if cat in query_text:
                    target_cat = cat
                    break
                
        reply_message = ""
        
        if db:
            try:
                # 1. 先去撈大倉庫裡面，該分類「尚未看過」的新聞（最前 5 則）
                docs = db.collection("news")\
                         .where("category", "==", target_cat)\
                         .where("viewed", "==", False)\
                         .limit(5)\
                         .stream()
                         
                chosen_docs = []
                news_list = []
                
                for doc in docs:
                    chosen_docs.append(doc)
                    data = doc.to_dict()
                    news_list.append(f"【{data.get('category')}】{data.get('title')}\n🔗 {data.get('url')}")
                
                # 2. 如果不夠 5 則，說明大倉庫已經被你看完了！觸發「大循環重置」
                if len(news_list) < 5:
                    # 撈出大倉庫裡該分類「所有看過」的新聞
                    all_viewed_docs = db.collection("news")\
                                        .where("category", "==", target_cat)\
                                        .where("viewed", "==", True)\
                                        .stream()
                    
                    # 批次把 viewed 全部改回 False
                    batch = db.batch()
                    reset_count = 0
                    for d in all_viewed_docs:
                        batch.update(d.reference, {"viewed": False})
                        reset_count += 1
                        if reset_count >= 400: # 避免批次超過 Firebase 單次上限
                            batch.commit()
                            batch = db.batch()
                            reset_count = 0
                    batch.commit()
                    
                    # 重置後重新補撈一次
                    retry_docs = db.collection("news")\
                                   .where("category", "==", target_cat)\
                                   .where("viewed", "==", False)\
                                   .limit(5)\
                                   .stream()
                    
                    chosen_docs = []
                    news_list = []
                    for doc in retry_docs:
                        chosen_docs.append(doc)
                        data = doc.to_dict()
                        news_list.append(f"【{data.get('category')}】{data.get('title')}\n🔗 {data.get('url')}")
                    
                    if news_list:
                        reply_message = f"🔄 提示：【{target_cat}】的新聞已被您全數看過一遍，已為您重置大循環！\n\n"
                
                # 3. 關鍵動作：把這次要秀給你看的 5 則新聞，在後台更新標記為 viewed = True
                if chosen_docs:
                    batch = db.batch()
                    for doc in chosen_docs:
                        batch.update(doc.reference, {"viewed": True})
                    batch.commit()
                    
                if news_list:
                    reply_message += f"🚀 為您調出最新【{target_cat}】新聞：\n\n" + "\n\n".join(news_list)
                else:
                    reply_message = f"🔍 目前資料庫中還沒有【{target_cat}】的新聞喔！\n💡 請先用瀏覽器打開網頁發動爬蟲儲存資料！"
                    
            except Exception as e:
                print(f"撈取不重複新聞失敗: {e}")
                reply_message = "❌ 資料庫查詢出了點狀況，請稍後再試！"

        return jsonify({
            "fulfillmentMessages": [{"text": {"text": [reply_message]}}]
        })

    # ==========================================================
    # 情況 B：你自己用瀏覽器打開網址 (GET) ➡️ 負責大量灌入新聞（不干涉 viewed）
    # ==========================================================
    target_categories = {
        "AI科技": "https://www.ettoday.net/news_search.php?keywords=AI",
        "3C": "https://game.ettoday.net/menu/3c/",
        "財經": "https://finance.ettoday.net/",
        "旅遊": "https://travel.ettoday.net/",
        "國際": "https://www.ettoday.net/news/focus/%E5%9C%8B%E9%9A%9B/"
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    summary = {}
    
    for cat_name, cat_url in target_categories.items():
        try:
            response = requests.get(cat_url, headers=headers, timeout=10, verify=False)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            news_links = soup.select('.part_pictxt_2 h3 a, .part_list_2 h3 a, .part_menu_2 h3 a, .piece h3 a, .box_1 h3 a, h3 a, .title a')
            
            seen_urls = set()
            count = 1
            db_save_count = 0
            
            for link in news_links:
                news_title = link.get_text().strip()
                news_href = link.get('href', '')
                if not news_title or len(news_title) < 10 or not news_href:
                    continue
                full_news_url = urljoin(cat_url, news_href)
                
                if full_news_url not in seen_urls and ("ettoday.net" in full_news_url):
                    seen_urls.add(full_news_url)
                    
                    if db:
                        doc_id = json.dumps(full_news_url).encode('utf-8')
                        doc_id_hash = hashlib.md5(doc_id).hexdigest()
                        doc_ref = db.collection("news").document(doc_id_hash)
                        
                        # 只有當這則新聞是「第一次被寫入資料庫」時，才設定 viewed = False
                        # 避免每次跑爬蟲都去把已經看完的新聞洗成 False。
                        if not doc_ref.get().exists:
                            doc_ref.set({
                                "category": cat_name,
                                "title": news_title,
                                "url": full_news_url,
                                "created_at": datetime.utcnow(),
                                "viewed": False  # 👈 核心關鍵欄位
                            })
                            db_save_count += 1
                    count += 1
            
            summary[cat_name] = f"掃描到 {count-1} 則 (全新儲入 {db_save_count} 則)"
            time.sleep(0.3)
        except Exception as e:
            summary[cat_name] = f"失敗: {e}"

    return jsonify({
        "status": "success",
        "message": "大倉庫新聞同步更新完成！輪流閱覽機制已就緒！",
        "result": summary
    })
@app.route("/webhook", methods=["POST"])
def webhook():
    req = request.get_json(force=True)
    action = req.get("queryResult").get("action")
    
    # 預設回傳訊息，防止 action 都不匹配時報錯
    info = "抱歉，我聽不懂你在說什麼。" 
    
    if action == "rateChoice":
        # 取得 Dialogflow 傳來的分級 (例如: "輔12級")
        rate = req.get("queryResult").get("parameters").get("rate")
        
        info = f"我是郭澔澄設計的電影聊天機器人，您選擇的分級是：{rate}，相關電影：\n\n"
        
        db = firestore.client()
        # 集合名稱改為 "本週新片含分級"
        collection_ref = db.collection("本週新片含分級")
        
        # 使用精確查詢
        docs = collection_ref.where("rate", "==", rate).get()
        
        result = ""
        for doc in docs:
            movie_data = doc.to_dict()
            title = movie_data.get("title", "未知片名")
            picture = movie_data.get("picture", "#")
            
            result += f"🎬 片名：{title}\n"
            result += f"🔗 圖片/連結：{picture}\n\n"
        
        if not result:
            result = f"找不到符合 {rate} 的電影，請確認分級輸入是否正確（例如：輔12級）。"
            
        info += result

    elif action == "input.unknown":
        # 設定希望限制的最大 Token 數
        ai_config = types.GenerateContentConfig(
            max_output_tokens=500
        )

        response = client.models.generate_content(
            model='gemini-3.1-flash-lite', # 註：目前官方正式版為 2.5，若您有特殊管道使用 3.5 請保持原樣
            contents=req["queryResult"]["queryText"],
            config=ai_config
        )
        
        # 修正縮排：確保 info 有正確賦值
        info = response.text
    
    else:
        # 當 action 都不匹配時的處理
        info = "Action 不匹配，無法處理此請求。"

    # 統一在最外層回傳給 Dialogflow
    return make_response(jsonify({"fulfillmentText": info}))

@app.route("/message")
def message():
    return render_template("message.html")

@app.route("/mis")
def course():
    return '<h1>資訊管理導論</h1><a href="/">回到網站</a>'

@app.route("/demo")
def demo():
    return render_template("demo.html")
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
    # 1. 取得參數並去除前後空白
    keyword = request.args.get("keyword", "").strip()
    
    # 2. 如果沒輸入關鍵字，顯示搜尋表單
    if not keyword:
        return """
            <h2>電影關鍵字查詢</h2>
            <form action="/movie3" method="get">
                <input type="text" name="keyword" placeholder="請輸入關鍵字 (如：沙)">
                <button type="submit">開始查詢</button>
            </form>
        """

    # 3. 連接 Firebase
    db = firestore.client()
    movies_ref = db.collection("電影2A")
    docs = movies_ref.stream()

    # 準備回傳的 HTML 內容
    info = f"<h3>關於『{keyword}』的查詢結果：</h3>"
    info += '<a href="/movie3">← 重新查詢</a><br><hr>'
    found = False

    # 4. 跑迴圈比對
    for doc in docs:
        movie = doc.to_dict()
        title = movie.get("title", "")
        
        # 【優化點】轉成小寫比對，實現更寬鬆的模糊搜尋
        if keyword.lower() in title.lower():
            found = True
            info += f"<b>電影名稱：</b>{title}<br>"
            info += f"<b>上映日期：</b>{movie.get('showDate', '暫無資料')}<br>"
            info += f"<b>片長：</b>{movie.get('showLength', '暫無資料')}<br>"
            # 防止圖片或連結不存在時程式出錯
            link = movie.get('hyperlink', '#')
            img_url = movie.get('picture', '')
            
            info += f"<b>詳細介紹：</b><a href='{link}' target='_blank'>開眼電影網網址</a><br>"
            if img_url:
                info += f"<img src='{img_url}' width='200'><br>"
            info += "<hr>"

    # 5. 沒找到時的處理
    if not found:
        return f"<h3>抱歉，找不到包含『{keyword}』的電影。</h3><a href='/movie3'>返回搜尋</a>"

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

@app.route("/road")
def road():
    R  = ""
    url = "https://newdatacenter.taichung.gov.tw/api/v1/no-auth/resource.download?rid=a1b899c0-511f-4e3d-b22b-814982a97e41"
    Data = requests.get(url)
    #print(Data.text)

    JsonData = json.loads(Data.text)
    for item in JsonData:
        R += item["路口名稱"] + ",總共發生" + item["總件數"] + "件事故<br>"
    return R + "<br><a href='/'>回首頁</a>"

@app.route("/rate")
def rate():
    #本週新片
    url = "https://www.atmovies.com.tw/movie/new/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text[5:]
    print(lastUpdate)
    print()

    result=sp.select(".filmList")

    for x in result:
        title = x.find("a").text
        introduce = x.find("p").text

        movie_id = x.find("a").get("href").replace("/", "").replace("movie", "")
        hyperlink = "http://www.atmovies.com.tw/movie/" + movie_id
        picture = "https://www.atmovies.com.tw/photo101/" + movie_id + "/pm_" + movie_id + ".jpg"

        r = x.find(class_="runtime").find("img")
        rate = ""
        if r != None:
            rr = r.get("src").replace("/images/cer_", "").replace(".gif", "")
            if rr == "G":
                rate = "普遍級"
            elif rr == "P":
                rate = "保護級"
            elif rr == "F2":
                rate = "輔12級"
            elif rr == "F5":
                rate = "輔15級"
            else:
                rate = "限制級"

        t = x.find(class_="runtime").text

        t1 = t.find("片長")
        t2 = t.find("分")
        showLength = t[t1+3:t2]

        t1 = t.find("上映日期")
        t2 = t.find("上映廳數")
        showDate = t[t1+5:t2-8]

        doc = {
            "title": title,
            "introduce": introduce,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "showLength": int(showLength),
            "rate": rate,
            "lastUpdate": lastUpdate
        }

        db = firestore.client()
        doc_ref = db.collection("本週新片含分級").document(movie_id)
        doc_ref.set(doc)
    return "本週新片已爬蟲及存檔完畢，網站最近更新日期為：" + lastUpdate

@app.route("/weather")
def weather():
    # 1. 從網址取得城市參數，預設為 "臺中市"
    city = request.args.get("city", "臺中市")
    city = city.replace("台", "臺")  # 統一轉換為「臺」以利 API 查詢

    # 2. CWA API 網址 (使用你圖片中的 Authorization Key)
    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization=rdec-key-123-45678-011121314&format=JSON&locationName=" + city

    try:
        data = requests.get(url)
        json_data = data.json()

        # 3. 檢查是否有抓到資料（避免輸入錯誤城市名導致當機）
        if not json_data["records"]["location"]:
            return f"<h3>找不到「{city}」的天氣資料，請檢查城市名稱是否正確。</h3><a href='/'>回首頁</a>"

        # 4. 解析氣象資料 (參考你圖片中的路徑)
        location_data = json_data["records"]["location"][0]
        
        # 天氣現象 (Wx)
        weather_state = location_data["weatherElement"][0]["time"][0]["parameter"]["parameterName"]
        
        # 降雨機率 (PoP)
        rain_chance = location_data["weatherElement"][1]["time"][0]["parameter"]["parameterName"]
        
        # 最低溫度 (MinT) - 額外增加的功能，讓資訊更完整
        min_temp = location_data["weatherElement"][2]["time"][0]["parameter"]["parameterName"]
        
        # 最高溫度 (MaxT)
        max_temp = location_data["weatherElement"][4]["time"][0]["parameter"]["parameterName"]

        # 5. 組合 HTML 介面
        html = f"""
            <h2>{city} 目前天氣預報</h2>
            <form action="/weather" method="get">
                切換縣市：<input type="text" name="city" placeholder="例如：臺北市">
                <button type="submit">查詢</button>
            </form>
            <hr>
            <p><b>天氣狀況：</b> {weather_state}</p>
            <p><b>降雨機率：</b> {rain_chance}%</p>
            <p><b>氣溫區間：</b> {min_temp}°C - {max_temp}°C</p>
            <br>
            <a href="/">回首頁</a>
        """
        return html

    except Exception as e:
        return f"天氣資料抓取失敗：{e} <br><a href='/'>回首頁</a>"


# 把 "你的_GEMINI_API_KEY_字串" 替換成你從 Google AI Studio 申請到的金鑰
client = genai.Client(api_key="AIzaSy...")
@app.route("/AI")
def AI():
    # 每次使用者拜訪該路徑時，直接使用全域的 client 呼叫模型
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents='我想查詢靜宜大學資管系的評價？',
    )
    
    # 回傳生成的文字
    return response.text

@app.route('/ask', methods=['GET', 'POST']) 
def ask():
    if request.method == "POST":
        user_prompt = request.form.get('prompt', '')
        if not user_prompt:
            return "請輸入內容", 400
        try:
            response = client.models.generate_content(
                model='gemini-3.5-flash',
                contents=user_prompt,
            )
            return response.text
        except Exception as e:
            return f"發生錯誤: {str(e)}", 500

    else:    
        # 當使用者直接打開網頁 (GET) 時，顯示輸入框畫面
        return render_template("ask.html")



if __name__ == "__main__":
    app.run(debug=True)

