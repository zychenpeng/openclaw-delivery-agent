"""
LINE Bot 對話邏輯
完整流程：文字 → Intent Parser → 搜尋 → 評分 → Flex Message
"""
import os
from concurrent.futures import ThreadPoolExecutor
from linebot.models import TextSendMessage, FlexSendMessage

# 導入 agent 模組
from agent.planner.intent_parser import IntentParser
from agent.planner.scorer import ScoringEngine
from agent.planner.recommender import RecommendationGenerator
from agent.scrapers.browser_manager import BrowserManager
from agent.scrapers.ubereats.search import UberEatsSearcher
from interfaces.line_bot.flex_messages import create_recommendations_flex

# 配置
PROFILE_PATH = os.path.join(os.path.dirname(__file__), "../../chromium_profile")

# 線程池（用於隔離同步 Playwright 代碼）
executor = ThreadPoolExecutor(max_workers=2)

def _search_restaurants_sync(search_query: str, limit: int = 15):
    """同步搜尋餐廳（完全隔離在獨立線程）"""
    from playwright.sync_api import sync_playwright
    
    print(f"[Thread] Starting browser for search: {search_query}")
    
    with sync_playwright() as p:
        # 啟動瀏覽器
        browser = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        try:
            # 取得或建立頁面
            if browser.pages:
                page = browser.pages[0]
            else:
                page = browser.new_page()
            
            # 執行搜尋
            searcher = UberEatsSearcher(page)
            results = searcher.search(search_query, limit=limit)
            
            print(f"[Thread] Search completed: {len(results)} results")
            return results
            
        finally:
            # 確保關閉瀏覽器
            browser.close()
            print(f"[Thread] Browser closed")

def handle_text_message(user_message: str, user_id: str):
    """
    處理用戶文字訊息
    
    Args:
        user_message: 用戶輸入的文字
        user_id: LINE 用戶 ID
    
    Returns:
        List of reply messages
    """
    # Step 1: 解析需求
    parser = IntentParser()
    intent = parser.parse(user_message)
    search_query = parser.to_search_query(intent)
    
    print(f"[Intent] Query: {search_query}, Budget: {intent.get('budget_max')}, Preferences: {intent.get('preferences')}")
    
    # Step 2: 搜尋餐廳（在獨立線程中運行同步代碼）
    future = executor.submit(_search_restaurants_sync, search_query, 15)
    restaurants = future.result(timeout=60)  # 60 秒超時
    
    print(f"[Search] Found {len(restaurants)} restaurants")
    
    if not restaurants:
        return [TextSendMessage(text="抱歉，找不到符合需求的餐廳 😢")]
    
    # Step 3: 評分排序
    scorer = ScoringEngine()
    scored_restaurants = scorer.score_restaurants(restaurants, intent)
    
    # Step 4: 生成推薦
    recommender = RecommendationGenerator()
    recommendations = recommender.generate_top_recommendations(scored_restaurants, intent, top_n=3)
    
    print(f"[Recommendations] Top 3: {[r['name'] for r in recommendations]}")
    
    # Step 5: 建立 Flex Message
    flex_message = create_recommendations_flex(recommendations, user_message)
    
    # 回傳訊息
    return [
        TextSendMessage(text=f"找到 {len(restaurants)} 家餐廳！為你推薦 Top 3："),
        flex_message
    ]
