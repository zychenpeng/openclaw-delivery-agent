"""
一次性腳本：從 persistent_context 匯出登入狀態
將 cookies 和 storage 儲存為 auth_state.json
"""
import os
from playwright.sync_api import sync_playwright

PROFILE_PATH = os.path.join(os.path.dirname(__file__), "chromium_profile")
AUTH_STATE_PATH = os.path.join(os.path.dirname(__file__), "auth_state.json")

def export_auth_state():
    """匯出登入狀態"""
    print("=" * 60)
    print("Exporting Auth State from Persistent Context")
    print("=" * 60)
    
    with sync_playwright() as p:
        print(f"\n[1/3] Launching persistent context from: {PROFILE_PATH}")
        
        context = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=False,  # 顯示瀏覽器，確認登入狀態
            args=['--disable-blink-features=AutomationControlled']
        )
        
        print(f"[2/3] Browser opened, please wait 5 seconds...")
        print("      (確認登入狀態，如果未登入請先登入)")
        
        # 開啟 Uber Eats 確認登入
        if context.pages:
            page = context.pages[0]
        else:
            page = context.new_page()
        
        page.goto("https://www.ubereats.com/tw")
        page.wait_for_timeout(5000)
        
        print(f"\n[3/3] Saving storage state to: {AUTH_STATE_PATH}")
        
        # 儲存 cookies 和 storage
        context.storage_state(path=AUTH_STATE_PATH)
        
        context.close()
        
        print("\n✅ Auth state exported successfully!")
        print(f"   Saved to: {AUTH_STATE_PATH}")
        print("=" * 60)

if __name__ == "__main__":
    export_auth_state()
