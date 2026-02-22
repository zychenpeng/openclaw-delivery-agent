"""
Phase 0.5b: 換一家正在營業的店測試完整流程
選擇「美味樂天派」測試加入購物車和結帳
"""
import os
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

# 路徑配置
PROFILE_PATH = os.path.join(os.path.dirname(__file__), "chromium_profile")
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "results")

def main():
    print("=" * 60)
    print("Phase 0.5b: Alternative Store Test")
    print("=" * 60)
    
    # 直接使用「美味樂天派」
    store_url = "https://www.ubereats.com/tw/store/美味樂天派/eixhCuEvUO2Z0E5RAFvAUA"
    store_name = "美味樂天派"
    
    print(f"\n[OK] Store: {store_name}")
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
        time.sleep(4)
        
        # 滾動一下確保菜單載入
        print("[*] Scrolling to load menu...")
        for i in range(3):
            page.evaluate("window.scrollBy(0, 400)")
            time.sleep(0.5)
        
        print("\n[*] Looking for available menu items...")
        
        # 找第一個可點擊的菜單項目（避開「暫時不提供」的）
        items = page.locator("li[role='button'], button").all()
        
        selected_item = None
        for idx, item in enumerate(items[:20]):  # 檢查前 20 個
            try:
                text = item.inner_text(timeout=500)
                
                # 跳過包含「暫時不提供」或「售完」的項目
                if "暫時不提供" in text or "售完" in text or "Unavailable" in text.lower():
                    continue
                
                # 跳過太短的文字（可能不是菜單項目）
                if len(text.strip()) < 3:
                    continue
                
                # 找到第一個看起來正常的項目
                if "$" in text or any(c.isdigit() for c in text):
                    selected_item = item
                    print(f"[OK] Found available item:")
                    print(f"     {text[:100]}")
                    break
                    
            except:
                continue
        
        if not selected_item:
            print("[ERROR] No available menu items found!")
            context.close()
            return
        
        # 點擊選中的項目
        print("\n[*] Clicking on item...")
        selected_item.click()
        time.sleep(3)
        
        # 處理可能的彈窗，找「加入購物車」按鈕
        print("[*] Looking for 'Add to cart' button...")
        add_cart_texts = [
            "加入購物車",
            "Add to cart",
            "加入訂單",
        ]
        
        for text in add_cart_texts:
            try:
                button = page.get_by_text(text, exact=False).first
                if button.is_visible(timeout=2000):
                    print(f"[OK] Found button: {text}")
                    button.click()
                    time.sleep(2)
                    break
            except:
                continue
        
        # 前往結帳
        print("\n[*] Going to checkout...")
        
        # 方法 1: 找結帳按鈕
        checkout_texts = ["前往結帳", "Checkout", "查看購物車", "View cart"]
        checkout_clicked = False
        
        for text in checkout_texts:
            try:
                button = page.get_by_text(text, exact=False).first
                if button.is_visible(timeout=2000):
                    print(f"[OK] Found checkout button: {text}")
                    button.click()
                    checkout_clicked = True
                    break
            except:
                continue
        
        # 方法 2: 找購物車圖示
        if not checkout_clicked:
            try:
                cart = page.locator("[data-testid*='cart'], [aria-label*='購物車'], [aria-label*='Cart']").first
                if cart.is_visible(timeout=2000):
                    print("[OK] Clicking cart icon")
                    cart.click()
                    checkout_clicked = True
            except:
                pass
        
        if not checkout_clicked:
            print("[WARN] Could not find checkout button, trying direct URL...")
            page.goto("https://www.ubereats.com/tw/checkout", timeout=10000)
        
        # 等待結帳頁面載入
        print("[*] Waiting for checkout page to fully load...")
        time.sleep(6)
        
        # 抓取結帳資訊
        print("\n[*] Extracting checkout information...")
        
        checkout_info = {
            "subtotal": None,
            "delivery_fee": None,
            "total": None,
        }
        
        try:
            page_text = page.inner_text("body")
            lines = [l.strip() for l in page_text.split("\n") if l.strip()]
            
            for line in lines:
                if "$" in line:
                    if "小計" in line or "Subtotal" in line.lower():
                        checkout_info["subtotal"] = line
                        print(f"  Found Subtotal: {line}")
                    elif "運費" in line or "delivery" in line.lower() or "fee" in line.lower():
                        checkout_info["delivery_fee"] = line
                        print(f"  Found Delivery: {line}")
                    elif "總計" in line or "Total" in line:
                        checkout_info["total"] = line
                        print(f"  Found Total: {line}")
        except Exception as e:
            print(f"[WARN] Failed to extract info: {e}")
        
        # 截圖
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(RESULTS_PATH, f"05b_checkout_{timestamp}.png")
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"\n[OK] Screenshot: {screenshot_path}")
        
        # 輸出 JSON
        result_data = {
            "timestamp": timestamp,
            "store_name": store_name,
            "store_url": store_url,
            "checkout_info": checkout_info,
        }
        
        json_path = os.path.join(RESULTS_PATH, f"05b_checkout_{timestamp}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        print(f"[OK] JSON saved: {json_path}")
        
        # 輸出摘要
        print("\n" + "=" * 60)
        print("RESULT")
        print("=" * 60)
        print(f"Store: {store_name}")
        print(f"Total: {checkout_info['total'] or 'N/A'}")
        print("\n[!] STOPPED AT CHECKOUT - NO PAYMENT ACTION")
        print("=" * 60)
        
        # 停留讓使用者檢視
        print("\n[*] Browser will stay open for 15 seconds for inspection...")
        time.sleep(15)
        
        context.close()
        print("[OK] Done!")

if __name__ == "__main__":
    main()
