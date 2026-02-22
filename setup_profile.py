"""
Setup Script: 建立 Chromium User Profile 並手動登入 Uber Eats
執行此腳本後，會開啟 Chromium 瀏覽器，你需要手動登入 Uber Eats。
登入完成後，關閉瀏覽器視窗，cookies 會自動保存到 profile 中。
"""
import os
from playwright.sync_api import sync_playwright

# Profile 路徑（會自動建立）
PROFILE_PATH = os.path.join(
    os.path.dirname(__file__), 
    "chromium_profile"
)

def setup_profile():
    print("=" * 60)
    print("Chromium User Profile Setup")
    print("=" * 60)
    print(f"\nProfile location: {PROFILE_PATH}")
    print("\nThis script will:")
    print("1. Launch Chromium with persistent profile")
    print("2. Navigate to Uber Eats Taiwan")
    print("3. Wait for you to manually login")
    print("4. Save cookies when you close the browser")
    print("\n" + "=" * 60)
    
    input("\nPress ENTER to launch Chromium...")
    
    with sync_playwright() as p:
        print("\n[*] Launching Chromium...")
        
        # 使用 persistent context 啟動（會保存 cookies/localStorage）
        context = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=False,  # 必須用有頭模式才能手動操作
            viewport={"width": 1280, "height": 800},
            locale="zh-TW",
            timezone_id="Asia/Taipei",
            args=[
                "--disable-blink-features=AutomationControlled",  # 隱藏自動化特徵
            ]
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        
        print("[*] Navigating to Uber Eats Taiwan...")
        try:
            page.goto("https://www.ubereats.com/tw", wait_until="networkidle", timeout=30000)
            print("[OK] Page loaded successfully!")
        except Exception as e:
            print(f"[WARNING] Page load issue: {e}")
            print("[*] Trying to continue anyway...")
        
        print("\n" + "=" * 60)
        print("MANUAL LOGIN REQUIRED")
        print("=" * 60)
        print("\nPlease complete these steps in the browser:")
        print("1. Click on login button")
        print("2. Enter your phone number / email")
        print("3. Complete OTP verification")
        print("4. Wait until you see your account icon (logged in)")
        print("5. (Optional) Set your default delivery address")
        print("\nCookies will be automatically saved to:")
        print(f"   {PROFILE_PATH}")
        print("\n" + "=" * 60)
        print("\nWhen you finish login, press ENTER here to close browser...")
        print("=" * 60)
        
        # 等待用戶按 Enter
        input("\n>>> Press ENTER to close browser and save profile: ")
        
        print("\n[*] Closing browser and saving profile...")
        context.close()
        
        print("[OK] Browser closed. Profile saved!")
        print(f"[OK] Profile location: {PROFILE_PATH}")

if __name__ == "__main__":
    setup_profile()
