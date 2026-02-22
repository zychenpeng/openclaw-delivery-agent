"""
Browser Manager - 統一管理 Playwright 瀏覽器實例
"""
import os
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

class BrowserManager:
    """管理持久化的 Chromium 瀏覽器實例"""
    
    def __init__(self, profile_path: str, headless: bool = False):
        self.profile_path = profile_path
        self.headless = headless
        self.playwright = None
        self.context = None
        
    def __enter__(self):
        """Context manager 進入"""
        self.playwright = sync_playwright().start()
        
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.profile_path,
            headless=self.headless,
            viewport={"width": 1280, "height": 900},
            locale="zh-TW",
            timezone_id="Asia/Taipei",
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        return self.context
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 退出"""
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()
    
    def get_page(self, context: BrowserContext) -> Page:
        """取得或建立新頁面"""
        if context.pages:
            return context.pages[0]
        return context.new_page()
