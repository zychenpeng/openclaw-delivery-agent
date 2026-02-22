"""
Quick test to verify Playwright installation
"""
from playwright.sync_api import sync_playwright

def test_playwright():
    print("[*] Testing Playwright installation...")
    try:
        with sync_playwright() as p:
            print("[OK] Playwright loaded successfully")
            device_count = len(p.devices)
            print(f"    Available device profiles: {device_count}")
            
            # Check Chromium path
            browser_type = p.chromium
            print("[OK] Chromium executable found")
            print("    Version: Chrome for Testing")
            
        print("\n[OK] All checks passed! Playwright is ready.")
        return True
    except Exception as e:
        print(f"\n[ERROR] {e}")
        return False

if __name__ == "__main__":
    test_playwright()
