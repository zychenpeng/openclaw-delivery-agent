"""
Debug 腳本：檢查搜尋結果頁面的實際 DOM 結構
找出正確的 URL 抓取 selector
"""
import os
import time
from agent.scrapers.browser_manager import BrowserManager

PROFILE_PATH = os.path.join(os.path.dirname(__file__), "chromium_profile")

def debug_search_structure():
    print("=" * 60)
    print("Debug: Search Result DOM Structure")
    print("=" * 60)
    
    with BrowserManager(PROFILE_PATH, headless=False) as context:
        page = context.pages[0] if context.pages else context.new_page()
        
        # 搜尋
        print("\n[1] Navigating to Uber Eats...")
        page.goto("https://www.ubereats.com/tw", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        
        # 找搜尋框
        print("[2] Finding search box...")
        search_box = page.locator("input[placeholder*='搜尋']").first
        search_box.click()
        time.sleep(0.5)
        search_box.fill("麻辣")
        time.sleep(0.5)
        search_box.press("Enter")
        
        print("[3] Waiting for results...")
        time.sleep(4)
        
        # 找第一個餐廳卡片
        print("\n[4] Analyzing first restaurant card...")
        
        # 嘗試找卡片
        cards = page.locator("[data-testid*='store-card']").all()
        
        if not cards:
            print("[ERROR] No cards found!")
            return
        
        first_card = cards[0]
        
        print(f"[OK] Found {len(cards)} cards")
        print("\n[5] First card analysis:")
        
        # 分析卡片結構
        print("\n--- Card outer HTML (first 500 chars) ---")
        try:
            html = first_card.evaluate("el => el.outerHTML")
            print(html[:500])
        except:
            pass
        
        print("\n--- Card tag name ---")
        try:
            tag = first_card.evaluate("el => el.tagName")
            print(tag)
        except:
            pass
        
        print("\n--- Card href attribute ---")
        try:
            href = first_card.get_attribute("href")
            print(f"href: {href}")
        except:
            print("No href on card itself")
        
        print("\n--- Links inside card ---")
        try:
            links = first_card.locator("a").all()
            print(f"Found {len(links)} <a> tags inside card")
            for idx, link in enumerate(links[:3]):
                href = link.get_attribute("href")
                text = link.inner_text(timeout=500) if href else "(no text)"
                print(f"  Link {idx+1}: {href}")
                print(f"           Text: {text[:50]}")
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n" + "=" * 60)
        print("Press Ctrl+C to close browser and continue...")
        print("=" * 60)
        
        # 保持瀏覽器開啟讓用戶檢視
        try:
            import signal
            signal.pause()
        except:
            time.sleep(60)

if __name__ == "__main__":
    debug_search_structure()
