"""
Phase 0.3: 搜尋餐廳並抓取基本資訊
測試搜尋功能，抓取餐廳的店名、ETA、評分
"""
import os
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

# 路徑配置
PROFILE_PATH = os.path.join(os.path.dirname(__file__), "chromium_profile")
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "results")

# 建立 results 資料夾
os.makedirs(RESULTS_PATH, exist_ok=True)

def search_restaurants(page, keyword, limit=6):
    """
    搜尋餐廳並抓取資訊
    """
    print(f"\n[*] Searching for: {keyword}")
    
    # 尋找搜尋框
    search_selectors = [
        "input[placeholder*='搜尋']",
        "input[placeholder*='Search']",
        "input[type='text'][name*='search']",
        "input[aria-label*='搜尋']",
        "[data-test*='search-input']",
    ]
    
    search_box = None
    for selector in search_selectors:
        try:
            search_box = page.locator(selector).first
            if search_box.is_visible(timeout=2000):
                print(f"[OK] Found search box: {selector}")
                break
        except:
            continue
    
    if not search_box:
        print("[ERROR] Search box not found!")
        return []
    
    # 輸入搜尋關鍵字
    search_box.click()
    time.sleep(0.5)
    search_box.fill(keyword)
    time.sleep(0.5)
    search_box.press("Enter")
    
    print("[*] Waiting for search results...")
    time.sleep(4)  # 等待搜尋結果載入
    
    # 抓取餐廳列表
    restaurants = []
    
    # 嘗試多種可能的餐廳卡片 selector
    card_selectors = [
        "[data-test*='store-card']",
        "[data-testid*='store-card']",
        "a[href*='/store/']",
        "div[role='article']",
        "article",
    ]
    
    cards = None
    for selector in card_selectors:
        try:
            cards = page.locator(selector).all()
            if len(cards) > 0:
                print(f"[OK] Found {len(cards)} results using: {selector}")
                break
        except:
            continue
    
    if not cards or len(cards) == 0:
        print("[WARN] No restaurant cards found")
        return []
    
    # 限制數量
    cards = cards[:limit]
    
    print(f"[*] Extracting data from {len(cards)} restaurants...")
    
    for idx, card in enumerate(cards, 1):
        try:
            restaurant = {
                "index": idx,
                "name": None,
                "eta": None,
                "rating": None,
                "url": None,
            }
            
            # 抓店名 - 嘗試多種方式
            name_selectors = [
                "h3", "h4", 
                "[data-test*='store-title']",
                "[data-testid*='store-title']",
                "span[class*='title']",
            ]
            
            for sel in name_selectors:
                try:
                    name_el = card.locator(sel).first
                    if name_el.is_visible(timeout=500):
                        restaurant["name"] = name_el.inner_text().strip()
                        break
                except:
                    continue
            
            # 抓 ETA (送達時間)
            eta_keywords = ["分鐘", "min", "mins", "時間"]
            try:
                text_content = card.inner_text()
                for line in text_content.split("\n"):
                    if any(kw in line for kw in eta_keywords):
                        restaurant["eta"] = line.strip()
                        break
            except:
                pass
            
            # 抓評分
            rating_selectors = [
                "[aria-label*='評分']",
                "[aria-label*='rating']",
                "svg ~ span",  # 星星圖示旁的文字
            ]
            
            for sel in rating_selectors:
                try:
                    rating_el = card.locator(sel).first
                    if rating_el.is_visible(timeout=500):
                        text = rating_el.inner_text().strip()
                        # 嘗試解析數字
                        if any(c.isdigit() for c in text):
                            restaurant["rating"] = text
                            break
                except:
                    continue
            
            # 嘗試抓取連結
            try:
                href = card.get_attribute("href")
                if href:
                    restaurant["url"] = href if href.startswith("http") else f"https://www.ubereats.com{href}"
            except:
                pass
            
            restaurants.append(restaurant)
            print(f"  [{idx}] {restaurant['name'] or '(無店名)'} | {restaurant['eta'] or 'N/A'} | {restaurant['rating'] or 'N/A'}")
            
        except Exception as e:
            print(f"  [WARN] Failed to extract restaurant {idx}: {e}")
            continue
    
    return restaurants

def main():
    print("=" * 60)
    print("Phase 0.3: Search Restaurants")
    print("=" * 60)
    
    keyword = "麻辣"
    
    with sync_playwright() as p:
        print("\n[*] Launching browser...")
        
        context = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=False,
            viewport={"width": 1280, "height": 800},
            locale="zh-TW",
            timezone_id="Asia/Taipei",
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        
        print("[*] Navigating to Uber Eats...")
        page.goto("https://www.ubereats.com/tw", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        
        # 執行搜尋
        restaurants = search_restaurants(page, keyword, limit=6)
        
        # 產生時間戳記
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 截圖
        screenshot_path = os.path.join(RESULTS_PATH, f"02_search_{timestamp}.png")
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"\n[OK] Screenshot: {screenshot_path}")
        
        # 輸出 JSON
        result_data = {
            "timestamp": timestamp,
            "keyword": keyword,
            "count": len(restaurants),
            "restaurants": restaurants,
        }
        
        json_path = os.path.join(RESULTS_PATH, f"02_search_{timestamp}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        print(f"[OK] JSON saved: {json_path}")
        
        # 輸出摘要
        print("\n" + "=" * 60)
        print("RESULT")
        print("=" * 60)
        print(f"Keyword: {keyword}")
        print(f"Found: {len(restaurants)} restaurants")
        print("=" * 60)
        
        # 短暫停留
        print("\n[*] Browser will close in 5 seconds...")
        time.sleep(5)
        
        context.close()
        print("[OK] Done!")

if __name__ == "__main__":
    main()
