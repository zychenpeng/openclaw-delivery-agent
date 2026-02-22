"""
Phase 0.4: 抓取餐廳菜單
從搜尋結果中選一家餐廳，進入店家頁面抓取菜單項目
"""
import os
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

# 路徑配置
PROFILE_PATH = os.path.join(os.path.dirname(__file__), "chromium_profile")
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "results")

def find_latest_search_result():
    """找到最新的搜尋結果 JSON"""
    json_files = [f for f in os.listdir(RESULTS_PATH) if f.startswith("02_search_") and f.endswith(".json")]
    if not json_files:
        return None
    latest = sorted(json_files)[-1]
    return os.path.join(RESULTS_PATH, latest)

def get_first_store_url(json_path):
    """從搜尋結果中取得第一家有 URL 的店"""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for restaurant in data["restaurants"]:
        if restaurant.get("url"):
            return restaurant["url"], restaurant.get("name", "Unknown")
    
    return None, None

def scrape_menu(page, limit=10):
    """抓取菜單項目 - 簡化版本，直接抓取所有文字分析"""
    print("\n[*] Waiting for menu to load...")
    time.sleep(3)
    
    # 滾動頁面觸發 lazy loading
    print("[*] Scrolling to load menu items...")
    for i in range(3):
        page.evaluate("window.scrollBy(0, 500)")
        time.sleep(0.5)
    
    # 方法：找所有包含 "$" 的元素作為菜單項目
    print("[*] Looking for items with prices...")
    
    # 抓取整個頁面內容，用最簡單的方式解析
    try:
        # 找所有 li 或 button 元素
        all_elements = page.locator("li, button, a").all()
        print(f"[*] Found {len(all_elements)} total elements, filtering for menu items...")
        
        menu_items = []
        
        for elem in all_elements:
            try:
                text = elem.inner_text(timeout=500)
                
                # 檢查是否包含價格符號
                if "$" not in text:
                    continue
                
                # 解析文字內容
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                
                item = {
                    "index": len(menu_items) + 1,
                    "name": None,
                    "price": None,
                    "raw_text": text[:100]  # 保留原始文字供 debug
                }
                
                # 找品項名稱（通常是最長的那行，且不含 $）
                for line in lines:
                    if "$" not in line and len(line) > 3:
                        item["name"] = line
                        break
                
                # 找價格（包含 $）
                for line in lines:
                    if "$" in line:
                        item["price"] = line
                        break
                
                if item["name"] or item["price"]:
                    menu_items.append(item)
                    print(f"  [{item['index']}] {item['name'] or '(無名稱)'} - {item['price'] or 'N/A'}")
                
                if len(menu_items) >= limit:
                    break
                    
            except:
                continue
        
        print(f"\n[OK] Extracted {len(menu_items)} menu items")
        return menu_items
        
    except Exception as e:
        print(f"[ERROR] Failed to scrape menu: {e}")
        return []

def main():
    print("=" * 60)
    print("Phase 0.4: Scrape Menu")
    print("=" * 60)
    
    # 讀取上一步的搜尋結果
    search_json = find_latest_search_result()
    if not search_json:
        print("\n[ERROR] No search result found!")
        print("Please run 02_search.py first.")
        return
    
    print(f"\n[*] Reading search result: {os.path.basename(search_json)}")
    
    store_url, store_name = get_first_store_url(search_json)
    if not store_url:
        print("[ERROR] No store with URL found in search results!")
        return
    
    print(f"[OK] Selected store: {store_name}")
    print(f"[OK] URL: {store_url}")
    
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
        
        print(f"[*] Navigating to store page...")
        page.goto(store_url, wait_until="domcontentloaded", timeout=30000)
        
        # 抓取菜單
        menu_items = scrape_menu(page, limit=10)
        
        # 產生時間戳記
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 截圖
        screenshot_path = os.path.join(RESULTS_PATH, f"03_menu_{timestamp}.png")
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"\n[OK] Screenshot: {screenshot_path}")
        
        # 輸出 JSON
        result_data = {
            "timestamp": timestamp,
            "store_name": store_name,
            "store_url": store_url,
            "menu_items_count": len(menu_items),
            "menu_items": menu_items,
        }
        
        json_path = os.path.join(RESULTS_PATH, f"03_menu_{timestamp}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        print(f"[OK] JSON saved: {json_path}")
        
        # 輸出摘要
        print("\n" + "=" * 60)
        print("RESULT")
        print("=" * 60)
        print(f"Store: {store_name}")
        print(f"Menu items: {len(menu_items)}")
        print("=" * 60)
        
        # 短暫停留
        print("\n[*] Browser will close in 5 seconds...")
        time.sleep(5)
        
        context.close()
        print("[OK] Done!")

if __name__ == "__main__":
    main()
