"""
Phase 0.5c: 分步驟截圖驗證完整流程
每個關鍵步驟都截圖，確保真的進入結帳頁面
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
    filename = f"05c_{step_name}_{timestamp}.png"
    path = os.path.join(RESULTS_PATH, filename)
    page.screenshot(path=path, full_page=True)
    print(f"[SCREENSHOT] {filename}")
    return path

def main():
    print("=" * 60)
    print("Phase 0.5c: Step-by-Step Verification")
    print("=" * 60)
    
    # 使用美味樂天派
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
            viewport={"width": 1280, "height": 800},
            locale="zh-TW",
            timezone_id="Asia/Taipei",
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        
        # === STEP 1: 店家頁面載入 ===
        print("\n[STEP 1] Loading store page...")
        page.goto(store_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        screenshots.append(save_screenshot(page, "step1_store_page", timestamp))
        
        # 滾動載入菜單
        print("[STEP 1] Scrolling to load menu...")
        for i in range(3):
            page.evaluate("window.scrollBy(0, 400)")
            time.sleep(0.5)
        
        # === STEP 2: 尋找並點擊菜單項目 ===
        print("\n[STEP 2] Finding menu item...")
        
        # 嘗試多種 selector
        selectors_to_try = [
            "li[role='button']",
            "button",
            "li",
            "a",
            "div[role='button']",
        ]
        
        selected_item = None
        item_text = None
        
        for selector in selectors_to_try:
            try:
                items = page.locator(selector).all()
                print(f"[STEP 2] Trying selector '{selector}', found {len(items)} elements")
                
                for item in items[:50]:
                    try:
                        text = item.inner_text(timeout=500)
                        
                        # 跳過太短的
                        if len(text.strip()) < 5:
                            continue
                        
                        # 跳過不可用的項目
                        if "暫時不提供" in text or "售完" in text or "Unavailable" in text:
                            continue
                        
                        # 找到有價格的項目（包含 $）
                        if "$" in text:
                            selected_item = item
                            item_text = text.replace("\n", " ")[:100]
                            print(f"[STEP 2] Found item: {item_text}")
                            break
                            
                    except:
                        continue
                
                if selected_item:
                    break
                    
            except Exception as e:
                print(f"[STEP 2] Selector '{selector}' failed: {e}")
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
        
        # === STEP 3: 確認加入購物車（處理彈窗） ===
        print("\n[STEP 3] Looking for 'Add to cart' button...")
        
        add_cart_found = False
        add_cart_texts = ["加入購物車", "Add to cart", "加入訂單"]
        
        for text in add_cart_texts:
            try:
                button = page.get_by_text(text, exact=False).first
                if button.is_visible(timeout=2000):
                    print(f"[STEP 3] Found: {text}")
                    button.click()
                    add_cart_found = True
                    time.sleep(2)
                    break
            except:
                continue
        
        if not add_cart_found:
            print("[STEP 3] No add-to-cart button found (might be auto-added)")
        
        screenshots.append(save_screenshot(page, "step3_after_add_cart", timestamp))
        
        # === STEP 4: 尋找並點擊「前往結帳」或購物車 ===
        print("\n[STEP 4] Looking for checkout/cart button...")
        
        checkout_clicked = False
        
        # 方法 1: 找「前往結帳」文字按鈕
        checkout_texts = ["前往結帳", "Checkout", "Go to checkout", "查看購物車"]
        for text in checkout_texts:
            try:
                button = page.get_by_text(text, exact=False).first
                if button.is_visible(timeout=2000):
                    print(f"[STEP 4] Found button: {text}")
                    button.click()
                    checkout_clicked = True
                    time.sleep(3)
                    break
            except:
                continue
        
        # 方法 2: 找購物車圖示
        if not checkout_clicked:
            try:
                cart = page.locator("[data-testid*='cart'], [aria-label*='Cart'], svg").filter(has_text="").first
                print("[STEP 4] Trying to click cart icon...")
                cart.click()
                checkout_clicked = True
                time.sleep(3)
            except Exception as e:
                print(f"[STEP 4] Cart icon click failed: {e}")
        
        if not checkout_clicked:
            print("[STEP 4] No checkout button found, will check current page")
        
        screenshots.append(save_screenshot(page, "step4_after_checkout_click", timestamp))
        
        # === STEP 5: 等待並確認結帳頁面 ===
        print("\n[STEP 5] Checking if on checkout page...")
        time.sleep(4)
        
        current_url = page.url
        print(f"[STEP 5] Current URL: {current_url}")
        
        # 檢查是否有結帳頁面的元素
        checkout_elements = {
            "delivery_address": False,
            "payment_method": False,
            "place_order": False,
        }
        
        page_text = page.inner_text("body")
        
        if "配送地址" in page_text or "Delivery address" in page_text or "地址" in page_text:
            checkout_elements["delivery_address"] = True
            print("[STEP 5] Found: Delivery address element")
        
        if "付款方式" in page_text or "Payment" in page_text or "支付" in page_text:
            checkout_elements["payment_method"] = True
            print("[STEP 5] Found: Payment method element")
        
        if "送出訂單" in page_text or "Place order" in page_text or "確認訂單" in page_text:
            checkout_elements["place_order"] = True
            print("[STEP 5] Found: Place order button")
        
        # 最終截圖
        screenshots.append(save_screenshot(page, "step5_final_page", timestamp))
        
        # === 結果分析 ===
        print("\n" + "=" * 60)
        print("VERIFICATION RESULT")
        print("=" * 60)
        print(f"URL: {current_url}")
        print(f"Delivery Address: {'YES' if checkout_elements['delivery_address'] else 'NO'}")
        print(f"Payment Method: {'YES' if checkout_elements['payment_method'] else 'NO'}")
        print(f"Place Order Button: {'YES' if checkout_elements['place_order'] else 'NO'}")
        
        is_checkout_page = any(checkout_elements.values())
        
        if is_checkout_page:
            print("\nStatus: ON CHECKOUT PAGE")
        else:
            print("\nStatus: NOT ON CHECKOUT PAGE")
        
        print("\nScreenshots saved:")
        for idx, path in enumerate(screenshots, 1):
            print(f"  {idx}. {os.path.basename(path)}")
        
        print("=" * 60)
        
        # 保存報告
        report = {
            "timestamp": timestamp,
            "store_name": store_name,
            "store_url": store_url,
            "selected_item": item_text,
            "final_url": current_url,
            "checkout_elements": checkout_elements,
            "is_checkout_page": is_checkout_page,
            "screenshots": [os.path.basename(s) for s in screenshots]
        }
        
        report_path = os.path.join(RESULTS_PATH, f"05c_report_{timestamp}.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\nReport saved: {report_path}")
        
        # 停留觀察
        print("\n[*] Browser will stay open for 15 seconds...")
        time.sleep(15)
        
        context.close()
        print("[OK] Done!")

if __name__ == "__main__":
    main()
