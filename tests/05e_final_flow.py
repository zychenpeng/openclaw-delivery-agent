"""
Phase 0.5e: 完整結帳流程（處理商品彈窗）
1. 點商品 → 彈窗出現（可能有附加選項）
2. 在彈窗內找「加入購物車」並點擊 → 彈窗消失
3. 點購物車圖示 → 側邊欄打開
4. 在側邊欄找「前往結帳」並點擊
5. 到達結帳頁面
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
    filename = f"05e_{step_name}_{timestamp}.png"
    path = os.path.join(RESULTS_PATH, filename)
    page.screenshot(path=path, full_page=False)  # 不要 full_page，避免太大
    print(f"[SCREENSHOT] {filename}")
    return path

def main():
    print("=" * 60)
    print("Phase 0.5e: Complete Checkout Flow")
    print("=" * 60)
    
    store_url = "https://www.ubereats.com/tw/store/美味樂天派/eixhCuEvUO2Z0E5RAFvAUA"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"\nTimestamp: {timestamp}\n")
    
    screenshots = []
    
    with sync_playwright() as p:
        print("[STEP 0] Launching browser...")
        
        context = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=False,
            viewport={"width": 1280, "height": 900},
            locale="zh-TW",
            timezone_id="Asia/Taipei",
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        
        # === STEP 1: 載入店家頁面 ===
        print("\n[STEP 1] Loading store page...")
        page.goto(store_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        
        # 滾動載入
        for i in range(3):
            page.evaluate("window.scrollBy(0, 400)")
            time.sleep(0.5)
        
        screenshots.append(save_screenshot(page, "step1_store", timestamp))
        
        # === STEP 2: 找商品並點擊 ===
        print("\n[STEP 2] Finding menu item...")
        
        # 直接找「烤吐司」
        try:
            item = page.get_by_text("烤吐司").first
            item.click()
            print("[STEP 2] Clicked: 烤吐司")
            time.sleep(2)
        except:
            print("[ERROR] Could not find menu item!")
            screenshots.append(save_screenshot(page, "error_no_item", timestamp))
            context.close()
            return
        
        screenshots.append(save_screenshot(page, "step2_item_clicked", timestamp))
        
        # === STEP 3: 處理商品彈窗，點「新增商品至訂單」按鈕 ===
        print("\n[STEP 3] Waiting for popup and looking for add button...")
        
        # 等待彈窗出現
        time.sleep(2)
        
        add_cart_success = False
        
        # 方法 1: 找包含「新增」「訂單」的按鈕（實際文字：新增 1 項商品至訂單）
        try:
            add_button = page.locator("button").filter(has_text="新增").filter(has_text="訂單").first
            if add_button.is_visible(timeout=3000):
                print("[STEP 3] Found 'Add to order' button (新增...訂單)")
                add_button.click()
                add_cart_success = True
                print("[STEP 3] Clicked! Waiting for popup to close...")
                time.sleep(2)
        except Exception as e:
            print(f"[STEP 3] Method 1 failed: {e}")
        
        # 方法 2: 找包含「至訂單」的按鈕
        if not add_cart_success:
            try:
                add_button = page.locator("button").filter(has_text="至訂單").first
                if add_button.is_visible(timeout=2000):
                    print("[STEP 3] Found button with '至訂單'")
                    add_button.click()
                    add_cart_success = True
                    time.sleep(2)
            except:
                pass
        
        # 方法 3: 找包含價格的大按鈕（底部黑色按鈕通常顯示價格）
        if not add_cart_success:
            try:
                add_button = page.locator("button").filter(has_text="$40").first
                if add_button.is_visible(timeout=2000):
                    print("[STEP 3] Found button with price")
                    add_button.click()
                    add_cart_success = True
                    time.sleep(2)
            except:
                pass
        
        if not add_cart_success:
            print("[ERROR] Could not find 'Add to cart' button!")
            print("[ERROR] Popup might still be open, taking screenshot...")
            screenshots.append(save_screenshot(page, "error_popup_stuck", timestamp))
            context.close()
            return
        
        screenshots.append(save_screenshot(page, "step3_after_add", timestamp))
        
        # === STEP 4: 確認購物車側邊欄是否已打開 ===
        print("\n[STEP 4] Checking if cart sidebar is open...")
        
        time.sleep(1)
        
        # 檢查是否有「前往結帳」按鈕可見（表示側邊欄已開）
        try:
            checkout_visible = page.locator("button").filter(has_text="前往結帳").first.is_visible(timeout=2000)
            if checkout_visible:
                print("[STEP 4] Cart sidebar is already open!")
            else:
                print("[STEP 4] Cart sidebar not visible, trying to open...")
                # 嘗試點購物車圖示
                cart = page.locator("[aria-label*='Cart']").first
                cart.click()
                time.sleep(2)
        except:
            # 如果找不到，可能側邊欄沒開，嘗試點購物車
            print("[STEP 4] Trying to click cart icon...")
            try:
                cart = page.locator("header button, nav button").last
                cart.click()
                time.sleep(2)
            except:
                pass
        
        screenshots.append(save_screenshot(page, "step4_cart_sidebar", timestamp))
        
        # === STEP 5: 在側邊欄找「前往結帳」按鈕 ===
        print("\n[STEP 5] Looking for checkout button in sidebar...")
        
        time.sleep(2)  # 多等一下確保側邊欄完全載入
        
        checkout_clicked = False
        
        # 方法 1: 用 get_by_text 直接找文字（最寬鬆）
        try:
            checkout_button = page.get_by_text("前往結帳").first
            if checkout_button.is_visible(timeout=3000):
                print("[STEP 5] Found checkout button by text")
                checkout_button.click()
                checkout_clicked = True
                print("[STEP 5] Clicked! Waiting for navigation...")
                time.sleep(5)
        except Exception as e:
            print(f"[STEP 5] Method 1 failed: {e}")
        
        # 方法 2: 找底部區域的大按鈕（通常結帳按鈕在底部且是黑色）
        if not checkout_clicked:
            try:
                # 找所有 button，選最後一個可見的大按鈕
                all_buttons = page.locator("button").all()
                print(f"[STEP 5] Found {len(all_buttons)} buttons total")
                
                for btn in reversed(all_buttons[-5:]):  # 檢查最後 5 個按鈕
                    try:
                        if btn.is_visible(timeout=500):
                            text = btn.inner_text(timeout=500)
                            if "前往" in text or "結帳" in text or "check" in text.lower():
                                print(f"[STEP 5] Found button with text: {text[:30]}")
                                btn.click()
                                checkout_clicked = True
                                time.sleep(5)
                                break
                    except:
                        continue
            except Exception as e:
                print(f"[STEP 5] Method 2 failed: {e}")
        
        if not checkout_clicked:
            print("[ERROR] Could not find checkout button!")
            print("[ERROR] Taking screenshot...")
            screenshots.append(save_screenshot(page, "error_no_checkout", timestamp))
            
            # Debug: 列出所有可見的文字
            try:
                visible_text = page.inner_text("body")
                print("\n[DEBUG] Visible text containing '結' or 'check':")
                for line in visible_text.split("\n"):
                    if "結" in line or "check" in line.lower():
                        print(f"  - {line.strip()}")
            except:
                pass
            
            context.close()
            return
        
        screenshots.append(save_screenshot(page, "step5_checkout_clicked", timestamp))
        
        # === STEP 6: 確認到達結帳頁面 ===
        print("\n[STEP 6] Verifying checkout page...")
        
        time.sleep(4)
        
        current_url = page.url
        print(f"[STEP 6] URL: {current_url}")
        
        is_checkout_url = "checkout" in current_url.lower()
        
        # 檢查結帳頁面元素
        page_text = page.inner_text("body")
        
        has_delivery = "配送地址" in page_text or "Delivery" in page_text
        has_payment = "付款方式" in page_text or "Payment" in page_text
        has_place_order = "送出訂單" in page_text or "Place order" in page_text
        
        print(f"  - Checkout URL: {is_checkout_url}")
        print(f"  - Delivery address: {has_delivery}")
        print(f"  - Payment method: {has_payment}")
        print(f"  - Place order button: {has_place_order}")
        
        screenshots.append(save_screenshot(page, "step6_final", timestamp))
        
        # === 結果 ===
        is_success = is_checkout_url or (has_delivery and has_payment)
        
        print("\n" + "=" * 60)
        if is_success:
            print("*** SUCCESS: REACHED CHECKOUT PAGE ***")
        else:
            print("*** FAILED: NOT ON CHECKOUT PAGE ***")
        print("=" * 60)
        
        print(f"\nFinal URL: {current_url}")
        print("\nScreenshots:")
        for idx, path in enumerate(screenshots, 1):
            print(f"  {idx}. {os.path.basename(path)}")
        
        # 保存報告
        report = {
            "timestamp": timestamp,
            "final_url": current_url,
            "is_checkout_url": is_checkout_url,
            "has_delivery_address": has_delivery,
            "has_payment_method": has_payment,
            "has_place_order_button": has_place_order,
            "is_success": is_success,
            "screenshots": [os.path.basename(s) for s in screenshots]
        }
        
        report_path = os.path.join(RESULTS_PATH, f"05e_report_{timestamp}.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\nReport: {os.path.basename(report_path)}")
        print("=" * 60)
        
        # 停留
        print("\n[*] Staying open for 15 seconds...")
        time.sleep(15)
        
        context.close()
        print("[OK] Done!")

if __name__ == "__main__":
    main()
