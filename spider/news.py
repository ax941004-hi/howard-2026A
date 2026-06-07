import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin
import urllib3

# 關閉跳過 SSL 驗證時產生的 Warning 警告文字
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def crawl_and_print_all_news():
    # 鎖定指定的 6 個分類
    target_categories = {
        "AI科技": "https://www.ettoday.net/news_search.php?keywords=AI",
        "3C": "https://game.ettoday.net/menu/3c/",
        "財經": "https://finance.ettoday.net/",
        "遊戲": "https://game.ettoday.net/",
        "旅遊": "https://travel.ettoday.net/",
        "國際": "https://www.ettoday.net/news/focus/%E5%9C%8B%E9%9A%9B/"
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    print("\n==================================================")
    print("🚀  ETtoday 6 大分類最新新聞【完整全量】爬取中...")
    print("==================================================\n")
    
    for cat_name, cat_url in target_categories.items():
        print(f"■ 正在讀取【{cat_name}】的所有最新消息...")
        
        try:
            response = requests.get(cat_url, headers=headers, timeout=10, verify=False)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 抓取該頁面上所有的標題與連結
            news_links = soup.select('.part_pictxt_2 h3 a, .part_list_2 h3 a, .piece h3 a, .box_1 h3 a, h3 a, .title a')
            
            seen_urls = set()
            count = 1
            
            print("┌" + "─" * 60)
            print(f"│ 分類：{cat_name}")
            print("├" + "─" * 60)
            
            for link in news_links:
                news_title = link.get_text().strip()
                news_href = link.get('href', '')
                
                # 過濾不合格的雜訊
                if not news_title or len(news_title) < 10 or not news_href:
                    continue
                if news_href.startswith('javascript'):
                    continue
                    
                full_news_url = urljoin(cat_url, news_href)
                
                if full_news_url not in seen_urls and ("ettoday.net" in full_news_url):
                    seen_urls.add(full_news_url)
                    
                    # 毫無保留直接印出
                    print(f"│ [{count}] {news_title}")
                    print(f"│     連結: {full_news_url}")
                    print(f"│ {'-' * 56}")
                    count += 1
                    
            if count == 1:
                print("│ 目前此頁面無即時新聞清單。")
            else:
                print(f"│ ⚙️ 本次成功列出 {count-1} 則【{cat_name}】的全部新聞")
            
            print("└" + "─" * 60 + "\n")
            
            # 禮貌歇息 0.5 秒
            time.sleep(0.5)
            
        except Exception as e:
            print(f"│ ❌ 抓取失敗，原因: {e}")
            print("└" + "─" * 60 + "\n")

    print("==================================================")
    print("🎉  所有分類的全部新聞已完整輸出完畢！")
    print("==================================================")

if __name__ == "__main__":
    crawl_and_print_all_news()