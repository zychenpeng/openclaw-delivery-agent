"""
Phase 0.5: 加入購物車並進入結帳頁面
測試完整流程：選擇商品 -> 加入購物車 -> 查看 checkout 總價
絕對不執行付款動作
"""
import os
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

# 路徑配置
PROFILE_PATH = os.path.join(os.path.dirname(__file__), "chromium_profile")
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "results")

def find_latest_menu_result():
    """找到最新的菜單結果 JSON"""
    json_files = [f for f in os.listdir(RESULTS_PATH) if f.startswith("03_menu_") and f.endswith(".json")]
    if not json_files:
        return None
    latest = sorted(json_files)[-1]
    return os.path.join(RESULTS_PATH, latest)

def add_item_to_cart(page, item_name):
    """尋找並點擊指定品項加入購物車"""
    print(f"\n[*] Looking for menu item...")
    
    # 滾動頁面確保項目可見
    for i in range(3):
        page.evaluate("window.scrollBy(0, 300)")
        time.sleep(0.3)
    
    # 嘗試找到包含品項名稱的元素並點擊
    try:
        # 方法 1: 直接用文字找按鈕
        item_button = page.get_by_text(item_name, exact=False).first
        if item_button.is_visible(timeout=3000):
            print(f"[OK] Found item button")
            item_button.click()
            time.sleep(2)
            return True
    except Exception as e:
        print(f"[WARN] Method 1 failed: {e}")
    
    # 方法 2: 找所有 li 或 button，檢查文字內容
    try:
        all_items = page.locator("li, button").all()
        for item in all_items:
            text = item.inner_text(timeout=500)
            if item_name in text or "麥克鷄塊" in text:
                print(f"[OK] Found item via text search")
                item.click()
                time.sleep(2)
                return True
    except Exception as e:
        print(f"[WARN] Method 2 failed: {e}")
    
    print("[ERROR] Item not found!")
    return False

def confirm_add_to_cart(page):
    """確認加入購物車（處理彈出視窗）"""
    print("\n[*] Looking for 'Add to cart' confirmation...")
    
    # 常見的「加入購物車」按鈕文字
    add_cart_texts = [
        "加入購物車",
        "Add to cart",
        "Add to order",
        "加入訂單",
    ]
    
    for text in add_cart_texts:
        try:
            button = page.get_by_text(text, exact=False).first
            if button.is_visible(timeout=2000):
                print(f"[OK] Found button: {text}")
                button.click()
                time.sleep(2)
                return True
        except:
            continue
    
    # 如果沒有彈窗，可能直接加入了
    print("[WARN] No confirmation dialog found (might be auto-added)")
    return True

def go_to_checkout(page):
    """進入結帳頁面"""
    print("\n[*] Going to checkout...")
    
    # 找「前往結帳」「查看購物車」等按鈕
    checkout_texts = [
        "前往結帳",
        "Go to checkout",
        "Checkout",
        "查看購物車",
        "View cart",
    ]
    
    for text in checkout_texts:
        try:
            button = page.get_by_text(text, exact=False).first
            if button.is_visible(timeout=2000):
                print(f"[OK] Found button: {text}")
                button.click()
                time.sleep(3)
                return True
        except:
            continue
    
    # 嘗試找購物車圖示點擊
    try:
        cart_icon = page.locator("[data-testid*='cart'], [aria-label*='購物車'], [aria-label*='Cart']").first
        if cart_icon.is_visible(timeout=2000):
            print("[OK] Found cart icon")
            cart_icon.click()
            time.sleep(3)
            return True
    except:
        pass
    
    print("[WARN] Checkout button not found")
    return False

def extract_checkout_info(page):
    """抓取結帳頁面資訊（總價、運費等）"""
    print("\n[*] Extracting checkout information...")
    
    time.sleep(2)
    
    info = {
        "subtotal": None,
        "delivery_fee": None,
        "total": None,
        "items": [],
    }
    
    # 抓取頁面所有文字，找包含 $ 的行
    try:
        page_text = page.inner_text("body")
        lines = [l.strip() for l in page_text.split("\n") if l.strip()]
        
        for line in lines:
            if "$" in line:
                # 嘗試辨識是哪種費用
                if "小計" in line or "Subtotal" in line.lower():
                    info["subtotal"] = line
                elif "運費" in line or "delivery" in line.lower() or "fee" in line.lower():
                    info["delivery_fee"] = line
                elif "總計" in line or "Total" in line or "total" in line.lower():
                    info["total"] = line
        
        # 打印找到的資訊
        print(f"  Subtotal: {info['subtotal'] or 'N/A'}")
        print(f"  Delivery: {info['delivery_fee'] or 'N/A'}")
        print(f"  Total: {info['total'] or 'N/A'}")
        
    except Exception as e:
        print(f"[WARN] Failed to extract checkout info: {e}")
    
    return info

def main():
    print("=" * 60)
    print("Phase 0.5: Add to Cart & Checkout")
    print("=" * 60)
    
    # 讀取上一步的菜單結果
    menu_json = find_latest_menu_result()
    if not menu_json:
        print("\n[ERROR] No menu result found!")
        print("Please run 03_scrape_menu.py first.")
        return
    
    print(f"\n[*] Reading menu result: {os.path.basename(menu_json)}")
    
    with open(menu_json, "r", encoding="utf-8") as f:
        menu_data = json.load(f)
    
    store_url = menu_data["store_url"]
    store_name = menu_data["store_name"]
    
    print(f"[OK] Store: {store_name}")
    
    # 目標商品（改用玉米湯，比較不會缺貨）
    target_item = "玉米湯"
    print(f"[OK] Target item: Corn Soup")
    
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
        time.sleep(3)
        
        # 步驟 1: 找商品並點擊
        if not add_item_to_cart(page, target_item):
            print("\n[ERROR] Failed to add item to cart!")
            context.close()
            return
        
        # 步驟 2: 確認加入購物車（處理彈窗）
        confirm_add_to_cart(page)
        
        # 步驟 3: 前往結帳
        if not go_to_checkout(page):
            print("\n[WARN] Could not find checkout button, trying manual navigation...")
            # 嘗試直接導航到購物車頁面
            try:
                page.goto("https://www.ubereats.com/tw/checkout", timeout=10000)
            except:
                pass
        
        # 額外等待確保結帳頁面完全載入
        print("[*] Waiting for checkout page to load...")
        time.sleep(5)
        
        # 步驟 4: 抓取結帳資訊
        checkout_info = extract_checkout_info(page)
        
        # 產生時間戳記
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 截圖
        screenshot_path = os.path.join(RESULTS_PATH, f"05_checkout_{timestamp}.png")
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"\n[OK] Screenshot: {screenshot_path}")
        
        # 輸出 JSON
        result_data = {
            "timestamp": timestamp,
            "store_name": store_name,
            "store_url": store_url,
            "target_item": target_item,
            "checkout_info": checkout_info,
        }
        
        json_path = os.path.join(RESULTS_PATH, f"05_checkout_{timestamp}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        print(f"[OK] JSON saved: {json_path}")
        
        # 輸出摘要
        print("\n" + "=" * 60)
        print("RESULT")
        print("=" * 60)
        print(f"Store: McDonald's")
        print(f"Item added: Corn Soup")
        print(f"Total: {checkout_info['total'] or 'N/A'}")
        print("\n[!] STOPPED AT CHECKOUT - NO PAYMENT ACTION")
        print("=" * 60)
        
        # 停留讓使用者檢視
        print("\n[*] Browser will stay open for 10 seconds for inspection...")
        time.sleep(10)
        
        context.close()
        print("[OK] Done!")

if __name__ == "__main__":
    main()
