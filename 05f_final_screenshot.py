"""
Phase 0.5f: 最終結帳頁面截圖
關掉加購彈窗，截一張乾淨的完整結帳頁面
"""
import os
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

# 路徑配置
PROFILE_PATH = os.path.join(os.path.dirname(__file__), "chromium_profile")
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "results")

def main():
    print("=" * 60)
    print("Phase 0.5f: Final Clean Checkout Screenshot")
    print("=" * 60)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    with sync_playwright() as p:
        print("\n[*] Launching browser...")
        
        context = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=False,
            viewport={"width": 1280, "height": 900},
            locale="zh-TW",
            timezone_id="Asia/Taipei",
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        
        # 直接去結帳頁面（應該會保留剛才的購物車狀態）
        print("[*] Navigating to checkout page...")
        page.goto("https://www.ubereats.com/tw/checkout", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        
        # 關掉「完成訂單」加購彈窗
        print("\n[*] Looking for 'Skip' button to close upsell popup...")
        
        skip_clicked = False
        
        # 方法 1: 找「跳過」按鈕
        try:
            skip_button = page.get_by_text("跳過").first
            if skip_button.is_visible(timeout=3000):
                print("[*] Found '跳過' button, clicking...")
                skip_button.click()
                skip_clicked = True
                time.sleep(2)
        except:
            print("[WARN] '跳過' button not found")
        
        # 方法 2: 找關閉按鈕（X）
        if not skip_clicked:
            try:
                close_button = page.locator("button[aria-label*='關閉'], button[aria-label*='Close']").first
                if close_button.is_visible(timeout=2000):
                    print("[*] Found close button, clicking...")
                    close_button.click()
                    time.sleep(2)
            except:
                print("[WARN] Close button not found")
        
        # 等待彈窗關閉
        time.sleep(2)
        
        # 截圖完整的結帳頁面
        print("\n[*] Taking final clean screenshot...")
        screenshot_path = os.path.join(RESULTS_PATH, f"05f_final_checkout_{timestamp}.png")
        page.screenshot(path=screenshot_path, full_page=True)
        
        print(f"\n[OK] Screenshot saved: {screenshot_path}")
        
        # 輸出當前 URL 確認
        current_url = page.url
        print(f"[OK] Current URL: {current_url}")
        
        print("\n" + "=" * 60)
        print("COMPLETE - Phase 0 Finished!")
        print("=" * 60)
        print("\nFinal checkout page screenshot ready for CIO review.")
        print(f"Screenshot: {os.path.basename(screenshot_path)}")
        print("\n[!] NO PAYMENT ACTION TAKEN - SAFE")
        print("=" * 60)
        
        # 停留觀察
        print("\n[*] Browser will stay open for 10 seconds...")
        time.sleep(10)
        
        context.close()
        print("\n[OK] Done! Phase 0 PoC Complete!")

if __name__ == "__main__":
    main()
