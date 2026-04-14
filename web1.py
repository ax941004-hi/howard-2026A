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


    return link
    return "歡迎進入郭澔澄的網站首頁2"

@app.route("/mis")
def course():
    return '<h1>資訊管理導論</h1><a href="/">回到網站</a>'


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

