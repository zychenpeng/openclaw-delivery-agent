"""
Phase 0.5d: 正確的結帳流程
按照 Uber Eats 實際流程：購物車側邊欄 → 前往結帳按鈕 → 結帳頁面
每一步都截圖驗證
"""
import os
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

# 路徑配置
PROFILE_PATH = os.path.join(os.path.dirname(__file__), "chromium_profile")
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "results")

def save_screenshot(page, step_name, timestamp):
    """保存截圖"""
    filename = f"05d_{step_name}_{timestamp}.png"
    path = os.path.join(RESULTS_PATH, filename)
    page.screenshot(path=path, full_page=True)
    print(f"[SCREENSHOT] {filename}")
    return path

def main():
    print("=" * 60)
    print("Phase 0.5d: Correct Checkout Flow")
    print("=" * 60)
    
    store_url = "https://www.ubereats.com/tw/store/美味樂天派/eixhCuEvUO2Z0E5RAFvAUA"
    store_name = "美味樂天派"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"\nStore: {store_name}")
    print(f"Timestamp: {timestamp}\n")
    
    screenshots = []
    
    with sync_playwright() as p:
        print("[STEP 0] Launching browser...")
        
        context = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=False,
            viewport={"width": 1280, "height": 900},
            locale="zh-TW",
            timezone_id="Asia/Taipei",
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        
        # === STEP 1: 載入店家頁面 ===
        print("\n[STEP 1] Loading store page...")
        page.goto(store_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        screenshots.append(save_screenshot(page, "step1_store_page", timestamp))
        
        # 滾動載入菜單
        for i in range(3):
            page.evaluate("window.scrollBy(0, 400)")
            time.sleep(0.5)
        
        # === STEP 2: 尋找並點擊菜單項目 ===
        print("\n[STEP 2] Finding menu item...")
        
        # 簡單策略：直接找包含 "$40" 這類價格的文字並點擊
        # 先找一個已知存在的商品名稱
        try:
            # 方法 1: 直接用文字找（從截圖看到有「烤吐司-巧克力」）
            item_locator = page.get_by_text("烤吐司").first
            if item_locator.is_visible(timeout=3000):
                print("[STEP 2] Found item by text: 烤吐司")
                selected_item = item_locator
                item_text = "烤吐司-巧克力"
            else:
                raise Exception("Not found")
        except:
            # 方法 2: 找所有 div 或 span，逐一檢查
            print("[STEP 2] Method 1 failed, trying alternative...")
            all_elements = page.locator("div, span, li, button").all()
            print(f"[STEP 2] Checking {min(len(all_elements), 100)} elements...")
            
            selected_item = None
            item_text = None
            
            for idx, elem in enumerate(all_elements[:100]):
                try:
                    text = elem.inner_text(timeout=1000)
                    
                    # 尋找包含 $ 且長度合理的文字
                    if "$" in text and 10 < len(text) < 200:
                        if "暫時不提供" not in text and "售完" not in text:
                            selected_item = elem
                            item_text = text.replace("\n", " ")[:100]
                            print(f"[STEP 2] Found item: {item_text}")
                            break
                except:
                    continue
        
        if not selected_item:
            print("[ERROR] No menu item found!")
            screenshots.append(save_screenshot(page, "error_no_item", timestamp))
            context.close()
            return
        
        print("[STEP 2] Clicking item...")
        selected_item.click()
        time.sleep(3)
        screenshots.append(save_screenshot(page, "step2_item_clicked", timestamp))
        
        # === STEP 3: 處理加入購物車彈窗 ===
        print("\n[STEP 3] Looking for 'Add to cart' button in popup...")
        
        add_cart_texts = ["加入購物車", "Add to cart", "加入訂單", "Add to order"]
        add_cart_found = False
        
        for text in add_cart_texts:
            try:
                button = page.get_by_text(text, exact=False).first
                if button.is_visible(timeout=2000):
                    print(f"[STEP 3] Found button: {text}")
                    button.click()
                    add_cart_found = True
                    time.sleep(2)
                    break
            except:
                continue
        
        if not add_cart_found:
            print("[STEP 3] No add-to-cart button found (might be auto-added)")
        
        screenshots.append(save_screenshot(page, "step3_after_add_cart", timestamp))
        
        # === STEP 4: 點擊購物車圖示，打開側邊欄 ===
        print("\n[STEP 4] Clicking cart icon to open sidebar...")
        
        cart_clicked = False
        
        # 嘗試多種購物車 selector
        cart_selectors = [
            "[data-testid='cart-button']",
            "[aria-label*='Cart']",
            "[aria-label*='購物車']",
            "button:has(svg)",  # 包含圖示的按鈕
        ]
        
        for selector in cart_selectors:
            try:
                cart = page.locator(selector).first
                if cart.is_visible(timeout=1000):
                    print(f"[STEP 4] Found cart using: {selector}")
                    cart.click()
                    cart_clicked = True
                    time.sleep(2)
                    break
            except:
                continue
        
        if not cart_clicked:
            print("[ERROR] Could not find cart icon!")
            screenshots.append(save_screenshot(page, "error_no_cart", timestamp))
            context.close()
            return
        
        screenshots.append(save_screenshot(page, "step4_cart_sidebar_open", timestamp))
        
        # === STEP 5: 在側邊欄中找「前往結帳」按鈕 ===
        print("\n[STEP 5] Looking for 'Go to checkout' button in sidebar...")
        
        checkout_button_texts = [
            "前往結帳",
            "Go to checkout",
            "Checkout",
            "結帳",
            "查看購物車",
            "View cart"
        ]
        
        checkout_button_found = False
        
        for text in checkout_button_texts:
            try:
                button = page.get_by_text(text, exact=False).first
                if button.is_visible(timeout=2000):
                    print(f"[STEP 5] Found button: {text}")
                    button.click()
                    checkout_button_found = True
                    time.sleep(3)
                    break
            except:
                continue
        
        if not checkout_button_found:
            print("[ERROR] Could not find checkout button in sidebar!")
            print("[ERROR] Taking screenshot for manual inspection...")
            screenshots.append(save_screenshot(page, "error_no_checkout_button", timestamp))
            
            # 輸出頁面文字幫助 debug
            page_text = page.inner_text("body")
            print("\n[DEBUG] Page contains these texts with 'checkout' or '結帳':")
            for line in page_text.split("\n"):
                if "checkout" in line.lower() or "結帳" in line or "前往" in line:
                    print(f"  - {line.strip()}")
            
            context.close()
            return
        
        screenshots.append(save_screenshot(page, "step5_after_checkout_click", timestamp))
        
        # === STEP 6: 確認已到達結帳頁面 ===
        print("\n[STEP 6] Waiting for checkout page to load...")
        time.sleep(5)
        
        current_url = page.url
        print(f"[STEP 6] Current URL: {current_url}")
        
        # 檢查 URL 是否包含 checkout
        is_checkout_url = "checkout" in current_url.lower()
        
        # 檢查頁面元素
        checkout_elements = {
            "delivery_address": False,
            "payment_method": False,
            "place_order": False,
        }
        
        page_text = page.inner_text("body")
        
        if "配送地址" in page_text or "Delivery address" in page_text or "送達" in page_text:
            checkout_elements["delivery_address"] = True
            print("[STEP 6] Found: Delivery address")
        
        if "付款方式" in page_text or "Payment" in page_text:
            checkout_elements["payment_method"] = True
            print("[STEP 6] Found: Payment method")
        
        if "送出訂單" in page_text or "Place order" in page_text:
            checkout_elements["place_order"] = True
            print("[STEP 6] Found: Place order button")
        
        screenshots.append(save_screenshot(page, "step6_checkout_page", timestamp))
        
        # === 結果分析 ===
        print("\n" + "=" * 60)
        print("VERIFICATION RESULT")
        print("=" * 60)
        print(f"Final URL: {current_url}")
        print(f"URL contains 'checkout': {is_checkout_url}")
        print(f"Delivery Address element: {'YES' if checkout_elements['delivery_address'] else 'NO'}")
        print(f"Payment Method element: {'YES' if checkout_elements['payment_method'] else 'NO'}")
        print(f"Place Order Button: {'YES' if checkout_elements['place_order'] else 'NO'}")
        
        is_checkout_page = is_checkout_url or any(checkout_elements.values())
        
        if is_checkout_page:
            print("\n*** SUCCESS: ON CHECKOUT PAGE ***")
        else:
            print("\n*** FAILED: NOT ON CHECKOUT PAGE ***")
        
        print("\nScreenshots saved:")
        for idx, path in enumerate(screenshots, 1):
            print(f"  {idx}. {os.path.basename(path)}")
        
        print("=" * 60)
        
        # 保存報告
        report = {
            "timestamp": timestamp,
            "store_name": store_name,
            "selected_item": item_text,
            "final_url": current_url,
            "is_checkout_url": is_checkout_url,
            "checkout_elements": checkout_elements,
            "is_checkout_page": is_checkout_page,
            "screenshots": [os.path.basename(s) for s in screenshots]
        }
        
        report_path = os.path.join(RESULTS_PATH, f"05d_report_{timestamp}.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\nReport: {report_path}")
        
        # 停留觀察
        print("\n[*] Browser will stay open for 15 seconds for inspection...")
        time.sleep(15)
        
        context.close()
        print("[OK] Done!")

if __name__ == "__main__":
    main()
