"""
測試重構後的 scraper 模組
驗證搜尋和菜單抓取功能
"""
import os
import json
from datetime import datetime
from agent.scrapers.browser_manager import BrowserManager
from agent.scrapers.ubereats.search import UberEatsSearcher
from agent.scrapers.ubereats.menu import UberEatsMenuScraper

# 配置
PROFILE_PATH = os.path.join(os.path.dirname(__file__), "chromium_profile")
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "results")

def test_search():
    """測試搜尋功能"""
    print("=" * 60)
    print("Test 1: Search Functionality")
    print("=" * 60)
    
    with BrowserManager(PROFILE_PATH, headless=False) as context:
        page = context.pages[0] if context.pages else context.new_page()
        
        searcher = UberEatsSearcher(page)
        
        # 搜尋「麻辣」
        results = searcher.search("麻辣", limit=5)
        
        print(f"\n[Result] Found {len(results)} unique restaurants:")
        for idx, restaurant in enumerate(results, 1):
            print(f"\n  {idx}. {restaurant['name']}")
            print(f"     Rating: {restaurant['rating']} ({restaurant['review_count']})")
            print(f"     ETA: {restaurant['eta']}")
            url = restaurant.get('url')
            if url:
                print(f"     URL: {url[:60]}...")
            else:
                print(f"     URL: (not found)")
        
        # 保存結果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(RESULTS_PATH, f"test_search_{timestamp}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n[Saved] {output_path}")
        
        return results

def test_menu(store_url: str):
    """測試菜單抓取功能"""
    print("\n" + "=" * 60)
    print("Test 2: Menu Scraping")
    print("=" * 60)
    
    with BrowserManager(PROFILE_PATH, headless=False) as context:
        page = context.pages[0] if context.pages else context.new_page()
        
        scraper = UberEatsMenuScraper(page)
        
        # 抓取店家資訊
        store_info = scraper.scrape_store(store_url, menu_limit=10)
        
        print(f"\n[Store Info]")
        print(f"  Name: {store_info['name']}")
        print(f"  Rating: {store_info['rating']} ({store_info['review_count']})")
        print(f"  Delivery Fee: {store_info['delivery_fee']}")
        print(f"  Service Fee: {store_info['service_fee']}")
        print(f"  Min Order: {store_info['min_order']}")
        
        print(f"\n[Menu Items] ({len(store_info['menu_items'])} items):")
        for idx, item in enumerate(store_info['menu_items'][:5], 1):
            print(f"  {idx}. {item['name']} - {item['price']}")
            if item['description']:
                print(f"     {item['description'][:50]}...")
        
        # 保存結果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(RESULTS_PATH, f"test_menu_{timestamp}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(store_info, f, ensure_ascii=False, indent=2)
        
        print(f"\n[Saved] {output_path}")
        
        return store_info

if __name__ == "__main__":
    print("\nTesting Refactored Scraper Modules\n")
    
    # Test 1: 搜尋
    search_results = test_search()
    
    # Test 2: 菜單抓取（用搜尋結果的第一家店）
    if search_results and search_results[0].get("url"):
        test_menu(search_results[0]["url"])
    else:
        print("\n[SKIP] No store URL found, skipping menu test")
    
    print("\n" + "=" * 60)
    print("[OK] All Tests Complete")
    print("=" * 60)
