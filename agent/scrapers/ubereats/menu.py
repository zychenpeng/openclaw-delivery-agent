"""
Uber Eats 菜單抓取
抓取單一店家的詳細資訊：菜單項目、費用、評分、營業時間等
"""
import time
from typing import List, Dict, Optional
from playwright.sync_api import Page

class UberEatsMenuScraper:
    """Uber Eats 店家菜單抓取器"""
    
    def __init__(self, page: Page):
        self.page = page
    
    def scrape_store(self, store_url: str, menu_limit: int = 20) -> Dict:
        """
        抓取店家完整資訊
        
        Args:
            store_url: 店家 URL
            menu_limit: 最多抓幾個菜單項目
        
        Returns:
            {
                "name": str,
                "rating": float,
                "review_count": str,
                "delivery_fee": str,
                "service_fee": str,
                "min_order": str,
                "menu_items": List[{name, price, description}]
            }
        """
        print(f"[UberEats Menu] Scraping: {store_url}")
        
        # 導航到店家頁面
        self.page.goto(store_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        
        # 滾動載入菜單
        for i in range(3):
            self.page.evaluate("window.scrollBy(0, 400)")
            time.sleep(0.5)
        
        # 抓取店家基本資訊
        store_info = {
            "name": self._extract_store_name(),
            "rating": self._extract_rating(),
            "review_count": self._extract_review_count(),
            "delivery_fee": self._extract_delivery_fee(),
            "service_fee": self._extract_service_fee(),
            "min_order": self._extract_min_order(),
            "menu_items": self._extract_menu_items(menu_limit),
        }
        
        print(f"[UberEats Menu] Extracted {len(store_info['menu_items'])} menu items")
        
        return store_info
    
    def _extract_store_name(self) -> Optional[str]:
        """抓取店名"""
        selectors = ["h1", "[data-testid='store-title']"]
        
        for selector in selectors:
            try:
                element = self.page.locator(selector).first
                if element.is_visible(timeout=2000):
                    return element.inner_text().strip()
            except:
                continue
        
        return None
    
    def _extract_rating(self) -> Optional[float]:
        """抓取評分"""
        try:
            page_text = self.page.inner_text("body")
            # 尋找格式如 "4.7" 的評分
            for line in page_text.split("\n"):
                line = line.strip()
                if len(line) > 1 and len(line) < 5:
                    try:
                        rating = float(line)
                        if 0 <= rating <= 5:
                            return rating
                    except:
                        continue
        except:
            pass
        
        return None
    
    def _extract_review_count(self) -> Optional[str]:
        """抓取評論數"""
        try:
            page_text = self.page.inner_text("body")
            for line in page_text.split("\n"):
                # 格式如 "(5,000+)" 或 "5000 ratings"
                if "(" in line and ")" in line and any(c.isdigit() for c in line):
                    return line.strip()
                if "rating" in line.lower() and any(c.isdigit() for c in line):
                    return line.strip()
        except:
            pass
        
        return None
    
    def _extract_delivery_fee(self) -> Optional[str]:
        """抓取運費"""
        try:
            page_text = self.page.inner_text("body")
            for line in page_text.split("\n"):
                line = line.strip()
                # 運費關鍵字
                if ("運費" in line or "delivery" in line.lower() or "fee" in line.lower()) and "$" in line:
                    return line
        except:
            pass
        
        return None
    
    def _extract_service_fee(self) -> Optional[str]:
        """抓取服務費"""
        try:
            page_text = self.page.inner_text("body")
            for line in page_text.split("\n"):
                line = line.strip()
                # 服務費關鍵字
                if ("服務費" in line or "service" in line.lower()) and "$" in line:
                    return line
        except:
            pass
        
        return None
    
    def _extract_min_order(self) -> Optional[str]:
        """抓取最低消費"""
        try:
            page_text = self.page.inner_text("body")
            for line in page_text.split("\n"):
                line = line.strip()
                # 最低消費關鍵字
                if ("最低" in line or "minimum" in line.lower()) and "$" in line:
                    return line
        except:
            pass
        
        return None
    
    def _extract_menu_items(self, limit: int) -> List[Dict]:
        """
        抓取菜單項目
        使用 Phase 0 驗證過的簡化策略：找所有包含 $ 的元素
        """
        menu_items = []
        
        try:
            # 找所有元素
            all_elements = self.page.locator("li, button, a").all()
            
            for elem in all_elements:
                try:
                    text = elem.inner_text(timeout=500)
                    
                    # 檢查是否包含價格
                    if "$" not in text:
                        continue
                    
                    # 解析文字
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    
                    item = {
                        "name": None,
                        "price": None,
                        "description": None,
                    }
                    
                    # 找品項名稱（最長的那行，且不含 $）
                    for line in lines:
                        if "$" not in line and len(line) > 3:
                            item["name"] = line
                            break
                    
                    # 找價格（包含 $）
                    for line in lines:
                        if "$" in line:
                            item["price"] = line
                            break
                    
                    # 找描述（第二長的不含 $ 的行）
                    desc_lines = [l for l in lines if "$" not in l and l != item["name"]]
                    if desc_lines:
                        item["description"] = desc_lines[0]
                    
                    # 過濾：至少要有名稱和價格
                    if item["name"] and item["price"]:
                        menu_items.append(item)
                    
                    if len(menu_items) >= limit:
                        break
                        
                except:
                    continue
        
        except Exception as e:
            print(f"[WARN] Menu extraction failed: {e}")
        
        # 去重（根據名稱）
        return self._deduplicate_menu_items(menu_items)
    
    def _deduplicate_menu_items(self, items: List[Dict]) -> List[Dict]:
        """菜單項目去重"""
        seen_names = set()
        unique_items = []
        
        for item in items:
            name = item.get("name")
            if name and name not in seen_names:
                unique_items.append(item)
                seen_names.add(name)
        
        return unique_items
