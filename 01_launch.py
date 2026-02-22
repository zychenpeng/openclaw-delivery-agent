"""
Phase 0.2: 啟動瀏覽器並檢查登入狀態
使用已建立的 chromium_profile 啟動，自動檢查登入狀態並截圖
"""
import os
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

# 路徑配置
PROFILE_PATH = os.path.join(os.path.dirname(__file__), "chromium_profile")
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "results")

# 建立 results 資料夾
os.makedirs(RESULTS_PATH, exist_ok=True)

def check_login_status(page):
    """
    檢查登入狀態
    Returns: (is_logged_in: bool, status_message: str)
    """
    print("\n[*] Checking login status...")
    
    # 等待頁面穩定
    time.sleep(2)
    
    # 方法 1: 尋找登入按鈕（如果存在表示未登入）
    login_button_selectors = [
        "text=登入",
        "text=Login",
        "text=Sign in",
        "[data-test='login-button']",
        "button:has-text('登入')",
    ]
    
    for selector in login_button_selectors:
        try:
            if page.locator(selector).first.is_visible(timeout=2000):
                return False, f"Found login button: {selector}"
        except:
            pass
    
    # 方法 2: 尋找帳號圖示/選單（存在表示已登入）
    account_selectors = [
        "[data-test='account-button']",
        "[data-test='user-account']",
        "button[aria-label*='帳戶']",
        "button[aria-label*='Account']",
        "[id*='account']",
        "svg[data-test='account-icon']",
    ]
    
    for selector in account_selectors:
        try:
            if page.locator(selector).first.is_visible(timeout=2000):
                return True, f"Found account element: {selector}"
        except:
            pass
    
    # 方法 3: 檢查 URL（有些網站登入後 URL 會改變）
    current_url = page.url
    if "login" in current_url.lower() or "signin" in current_url.lower():
        return False, f"URL contains login keyword: {current_url}"
    
    return None, "Unable to determine login status"

def launch_and_check():
    """主要執行流程"""
    print("=" * 60)
    print("Phase 0.2: Launch Browser & Check Login Status")
    print("=" * 60)
    print(f"\nProfile: {PROFILE_PATH}")
    print(f"Results: {RESULTS_PATH}")
    print("=" * 60)
    
    if not os.path.exists(PROFILE_PATH):
        print("\n[ERROR] Profile not found!")
        print(f"Please run setup_profile.py first to create profile at:")
        print(f"  {PROFILE_PATH}")
        return
    
    with sync_playwright() as p:
        print("\n[*] Launching Chromium with saved profile...")
        
        # 使用已存在的 profile 啟動
        context = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=False,  # 可視化執行，方便觀察
            viewport={"width": 1280, "height": 800},
            locale="zh-TW",
            timezone_id="Asia/Taipei",
            args=[
                "--disable-blink-features=AutomationControlled",
            ]
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        
        print("[*] Navigating to Uber Eats Taiwan...")
        try:
            page.goto("https://www.ubereats.com/tw", wait_until="domcontentloaded", timeout=30000)
            print("[OK] Page loaded")
        except Exception as e:
            print(f"[WARNING] Page load issue: {e}")
            print("[*] Continuing anyway...")
        
        # 額外等待確保動態內容載入
        time.sleep(3)
        
        # 檢查登入狀態
        is_logged_in, status_msg = check_login_status(page)
        
        # 產生時間戳記
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 截圖
        screenshot_path = os.path.join(RESULTS_PATH, f"01_launch_{timestamp}.png")
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"\n[OK] Screenshot saved: {screenshot_path}")
        
        # 輸出結果
        print("\n" + "=" * 60)
        print("RESULT")
        print("=" * 60)
        print(f"URL: {page.url}")
        print(f"Login Status: {status_msg}")
        
        if is_logged_in is True:
            print("[OK] LOGGED IN")
        elif is_logged_in is False:
            print("[FAIL] NOT LOGGED IN")
        else:
            print("[WARN] UNKNOWN STATUS")
        
        print("=" * 60)
        
        # 短暫停留讓使用者確認
        print("\n[*] Browser will close in 5 seconds...")
        time.sleep(5)
        
        context.close()
        print("\n[OK] Browser closed")

if __name__ == "__main__":
    launch_and_check()
