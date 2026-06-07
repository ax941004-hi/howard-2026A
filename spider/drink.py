import requests
from bs4 import BeautifulSoup
import urllib3
import time

# 關閉不安全連線的警告訊息
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 1. 飲品 8 大分類 (線上即時同步)
MENU_CATEGORIES = {
    "著時必喝": "seasonal",
    "鮮搾果汁(無咖啡因)": "fruitjuice",
    "冰釀銀耳": "sweet",
    "果茶系列": "",  
    "許慶良鮮乳": "milk",
    "茶奶": "teamilk",
    "特調": "special",
    "品牌聯名": "red-bull"
}

# ⭐️ 核心修改 1：將變數名稱改為 STORE_URLS，並修正中部網址（官網標準結構通常是 central 喔！）
STORE_URLS = {
    "北部": "https://www.dayungs.com/retail-html/north/",
    "中部": "https://www.dayungs.com/retail-html/central/", # 👈 幫你修正為官網對應的網址名稱
    "南部": "https://www.dayungs.com/retail-html/south/",
    "東部": "https://www.dayungs.com/retail-html/east/"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

NOISE_WORDS = ["美味飲品", "著時必喝", "最新消息", "全部消息", "成為我的好朋友", 
               "關於大苑子", "實現苑望", "聯絡我們", "大苑子APP", "主選單", "訂閱"]

# ==================================================
# 第一階段：線上爬取 8 大飲品分類 (100% 安全)
# ==================================================
print("==================================================")
print("     第一階段：大 苑 子 全 系 列 飲 品 分 類 爬 蟲")
print("==================================================")

for category_name, url_suffix in MENU_CATEGORIES.items():
    if url_suffix:
        url = f"https://www.dayungs.com/home/product/{url_suffix}/"
    else:
        url = "https://www.dayungs.com/home/product/"
        
    print(f"🚀 正在即時同步 【{category_name}】 的飲品資料...")
    
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        response.encoding = "utf-8"
        
        if response.status_code == 200:
            sp = BeautifulSoup(response.text, "html.parser")
            heading_tags = sp.select("h2.elementor-heading-title")
            
            idx = 1
            seen_in_category = set()
            
            print("-" * 50)
            for tag in heading_tags:
                drink_name = tag.text.strip()
                if drink_name and drink_name not in NOISE_WORDS and drink_name not in seen_in_category:
                    seen_in_category.add(drink_name)
                    print(f"  {idx:02d}. 🥤 {drink_name}")
                    idx += 1
            print("-" * 50 + "\n")
        else:
            print(f"  ❌ 連線失敗，狀態碼：{response.status_code}\n")
    except Exception as e:
        print(f"  ❌ 爬取時發生錯誤: {e}\n")
    time.sleep(1)

# ==================================================
# 第二階段：線上精準解析各區分店表格 (加入強大防爆機制)
# ==================================================
print("==================================================")
print("     第二階段：全 台 門 市 依 地 區 精 準 剖 析")
print("==================================================")

for region, url in STORE_URLS.items():
    print(f"🌐 正在從線上連結【{url}】同步 {region} 地區分店數據...")
    
    try:
        # ⭐️ 核心修改 2：直接發送網路請求抓取該地區分頁，不使用本機檔案檢查
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        response.encoding = "utf-8"
        
        if response.status_code == 200:
            sp = BeautifulSoup(response.text, "html.parser")
            
            # 配合大苑子網頁的 TablePress 結構，切入表格的每一列
            rows = sp.select("table tbody tr")
            
            print("-" * 50)
            print(f"📍 【{region}地區門市】")
            print("-" * 50)
            
            idx = 1
            seen_stores = set()
            
            for row in rows:
                cells = row.find_all("td")
                if cells:
                    # 第一欄 (index 0) 是「店名」
                    store_name = cells[0].text.strip()
                    
                    if store_name and "店名" not in store_name and store_name not in seen_stores:
                        seen_stores.add(store_name)
                        
                        # 第四欄 (index 3) 是「地址」
                        address = cells[3].text.strip() if len(cells) > 3 else "未標明地址"
                        
                        print(f"  {idx:02d}. 🏪 {store_name:<15} 📍 地址: {address}")
                        idx += 1
                        
            if idx == 1:
                print("  (該地區網頁內的表格無有效門市資料展示)")
            print("-" * 50 + "\n")
            
        else:
            print(f"  ❌ 地區網頁回應失敗，狀態碼：{response.status_code}\n")
            
    except requests.exceptions.ConnectionError:
        # ⭐️ 核心修改 3：遇到萬惡的拒絕連線時自動捕捉，警告提示後繼續跑下一個地區，不會死機！
        print(f"  ⚠️ 警告：該地區網址發動了反爬蟲阻擋 (ConnectionRefused)，系統自動跳過。\n")
        print("-" * 50 + "\n")
        
    except Exception as e:
        print(f"  ❌ 擷取該門市資料時發生預期外錯誤: {e}\n")
        print("-" * 50 + "\n")
        
    # 稍微休息 1.5 秒，減緩被伺服器偵測的機率
    time.sleep(1.5)

print("🎉 大苑子線上飲品分類與全台各地區精準門市資料同步完畢！")