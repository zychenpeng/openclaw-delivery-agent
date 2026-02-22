"""
Uber Eats 搜尋功能
從關鍵字搜尋餐廳，回傳結構化的店家列表
"""
import time
from typing import List, Dict, Optional
from playwright.sync_api import Page

class UberEatsSearcher:
    """Uber Eats 餐廳搜尋器"""
    
    BASE_URL = "https://www.ubereats.com/tw"
    
    def __init__(self, page: Page):
        self.page = page
    
    def search(self, keyword: str, limit: int = 10) -> List[Dict]:
        """
        搜尋餐廳
        
        Args:
            keyword: 搜尋關鍵字
            limit: 最多回傳幾家店
        
        Returns:
            List of {name, eta, rating, review_count, url}
        """
        print(f"[UberEats] Searching for: {keyword}")
        
        # 導航到首頁
        self.page.goto(self.BASE_URL, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        
        # 找搜尋框並輸入關鍵字
        search_box = self._find_search_box()
        if not search_box:
            raise Exception("Search box not found")
        
        search_box.click()
        time.sleep(0.5)
        search_box.fill(keyword)
        time.sleep(0.5)
        search_box.press("Enter")
        
        print("[UberEats] Waiting for search results...")
        time.sleep(4)
        
        # 抓取餐廳卡片
        raw_results = self._extract_restaurant_cards()
        
        # 去重 + 限制數量
        deduplicated = self._deduplicate_results(raw_results)
        limited = deduplicated[:limit]
        
        print(f"[UberEats] Found {len(raw_results)} raw → {len(deduplicated)} unique → {len(limited)} returned")
        
        return limited
    
    def _find_search_box(self) -> Optional[any]:
        """找搜尋框"""
        selectors = [
            "input[placeholder*='搜尋']",
            "input[placeholder*='Search']",
            "input[type='text'][name*='search']",
        ]
        
        for selector in selectors:
            try:
                box = self.page.locator(selector).first
                if box.is_visible(timeout=2000):
                    return box
            except:
                continue
        
        return None
    
    def _extract_restaurant_cards(self) -> List[Dict]:
        """抓取餐廳卡片資訊"""
        results = []
        
        # 嘗試多種 selector
        card_selectors = [
            "[data-testid*='store-card']",
            "a[href*='/store/']",
        ]
        
        cards = []
        for selector in card_selectors:
            try:
                cards = self.page.locator(selector).all()
                if len(cards) > 0:
                    print(f"[UberEats] Found {len(cards)} cards using: {selector}")
                    break
            except:
                continue
        
        if not cards:
            print("[WARN] No restaurant cards found")
            return []
        
        # 逐一解析卡片
        for card in cards:
            try:
                restaurant = self._parse_card(card)
                if restaurant and restaurant.get("name"):  # 至少要有店名
                    results.append(restaurant)
            except Exception as e:
                # 個別卡片解析失敗不中斷整個流程
                continue
        
        return results
    
    def _parse_card(self, card) -> Dict:
        """解析單一餐廳卡片"""
        restaurant = {
            "name": None,
            "eta": None,
            "rating": None,
            "review_count": None,
            "url": None,
        }
        
        # 抓店名
        name_selectors = ["h3", "h4", "[data-test*='store-title']"]
        for sel in name_selectors:
            try:
                name_el = card.locator(sel).first
                if name_el.is_visible(timeout=500):
                    restaurant["name"] = name_el.inner_text().strip()
                    break
            except:
                continue
        
        # 抓 ETA（送達時間）
        try:
            text = card.inner_text()
            for line in text.split("\n"):
                if "分鐘" in line or "min" in line.lower():
                    restaurant["eta"] = line.strip()
                    break
        except:
            pass
        
        # 抓評分和評論數
        try:
            text = card.inner_text()
            for line in text.split("\n"):
                # 格式通常是 "4.9\n(5,000+)" 或 "4.9 (5,000+)"
                if any(c.isdigit() for c in line) and ("." in line or "(" in line):
                    parts = line.split("(")
                    if len(parts) >= 1:
                        # 評分
                        rating_part = parts[0].strip()
                        try:
                            rating = float(rating_part)
                            restaurant["rating"] = rating
                        except:
                            pass
                    
                    if len(parts) >= 2:
                        # 評論數
                        review_part = parts[1].replace(")", "").strip()
                        restaurant["review_count"] = review_part
                    break
        except:
            pass
        
        # 抓 URL（多種方法）
        try:
            # 方法 1: 卡片本身是 <a> 標籤
            tag_name = card.evaluate("el => el.tagName").upper()
            if tag_name == "A":
                href = card.get_attribute("href")
                if href:
                    restaurant["url"] = self._normalize_url(href)
            
            # 方法 2: 卡片內部第一個連結
            if not restaurant["url"]:
                links = card.locator("a[href*='/store/']").all()
                if links:
                    href = links[0].get_attribute("href")
                    if href:
                        restaurant["url"] = self._normalize_url(href)
            
            # 方法 3: 任何包含 /store/ 的連結
            if not restaurant["url"]:
                all_links = card.locator("a").all()
                for link in all_links:
                    href = link.get_attribute("href")
                    if href and "/store/" in href:
                        restaurant["url"] = self._normalize_url(href)
                        break
        except:
            pass
        
        return restaurant
    
    def _normalize_url(self, href: str) -> str:
        """標準化 URL"""
        if href.startswith("http"):
            return href
        elif href.startswith("/"):
            return f"https://www.ubereats.com{href}"
        else:
            return f"https://www.ubereats.com/{href}"
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """
        去重（根據店名和 URL）
        同一家店可能出現多次（不同 DOM 元素）
        """
        seen_names = set()
        seen_urls = set()
        unique_results = []
        
        for restaurant in results:
            name = restaurant.get("name")
            url = restaurant.get("url")
            
            # 用名字或 URL 判斷是否重複
            key = url if url else name
            
            if key and key not in seen_urls and name not in seen_names:
                unique_results.append(restaurant)
                if url:
                    seen_urls.add(url)
                if name:
                    seen_names.add(name)
        
        return unique_results
