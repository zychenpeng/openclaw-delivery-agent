"""
Background Worker V2 - 使用 storage_state 取代 persistent_context
使用 async Playwright + storage_state，完全相容 FastAPI
"""
import asyncio
import os
from linebot import LineBotApi
from linebot.models import TextSendMessage
from playwright.async_api import async_playwright, Browser

# 導入 agent 模組
from agent.planner.intent_parser import IntentParser
from agent.planner.scorer import ScoringEngine
from agent.planner.recommender import RecommendationGenerator
from interfaces.line_bot.flex_messages import create_recommendations_flex

# 配置
AUTH_STATE_PATH = os.path.join(os.path.dirname(__file__), "../../auth_state.json")

# 全域 Queue 和 Browser
task_queue = asyncio.Queue()
global_browser: Browser = None
global_playwright = None

async def init_browser():
    """初始化全域 browser（app 啟動時調用一次）"""
    global global_browser, global_playwright
    
    print("[Browser] Initializing global browser...")
    
    global_playwright = await async_playwright().start()
    global_browser = await global_playwright.chromium.launch(
        headless=True,
        args=['--disable-blink-features=AutomationControlled']
    )
    
    print("[Browser] Global browser initialized")

async def close_browser():
    """關閉全域 browser（app 關閉時調用）"""
    global global_browser, global_playwright
    
    if global_browser:
        print("[Browser] Closing global browser...")
        await global_browser.close()
        global_browser = None
    
    if global_playwright:
        await global_playwright.stop()
        global_playwright = None
    
    print("[Browser] Global browser closed")

async def search_and_recommend(user_message: str) -> dict:
    """
    async 函數：執行搜尋 + 評分 + 推薦
    使用 new_context(storage_state) 載入 cookies
    
    Returns:
        {
            'success': bool,
            'recommendations': list,
            'total_found': int,
            'error': str (if failed)
        }
    """
    print(f"\n[Worker] Processing task: {user_message}")
    
    # Step 1: 解析需求
    parser = IntentParser()
    intent = parser.parse(user_message)
    search_query = parser.to_search_query(intent)
    
    print(f"[Worker] Intent parsed: {search_query}")
    
    # Step 2: 建立新 context（載入 cookies）
    context = await global_browser.new_context(
        storage_state=AUTH_STATE_PATH
    )
    
    try:
        page = await context.new_page()
        
        # 前往 Uber Eats 搜尋
        print(f"[Worker] Navigating to Uber Eats...")
        await page.goto("https://www.ubereats.com/tw")
        await page.wait_for_timeout(2000)
        
        # 搜尋
        print(f"[Worker] Searching for: {search_query}")
        
        # 找搜尋框並輸入
        search_input = page.locator('input[data-testid="search-suggestions-input"]')
        if await search_input.count() > 0:
            await search_input.fill(search_query)
            await search_input.press("Enter")
            await page.wait_for_timeout(3000)
        else:
            # 備用方案：直接導航到搜尋結果頁
            await page.goto(f"https://www.ubereats.com/tw/search?q={search_query}")
            await page.wait_for_timeout(5000)
        
        # 等待搜尋結果
        print(f"[Worker] Waiting for search results...")
        await page.wait_for_selector('[data-testid*="store-card"]', timeout=10000)
        
        # 抓取餐廳資訊
        print(f"[Worker] Extracting restaurant data...")
        cards = await page.locator('[data-testid*="store-card"]').all()
        
        restaurants = []
        for idx, card in enumerate(cards[:15]):  # 限制 15 家
            try:
                # 店名
                name_elem = card.locator('h3')
                name = await name_elem.inner_text() if await name_elem.count() > 0 else f"店家 {idx+1}"
                
                # 評分（精確選擇器：包含「評分」或「顆星」）
                rating_elem = card.locator('[aria-label*="評分"]').first
                rating_text = None
                if await rating_elem.count() > 0:
                    aria_label = await rating_elem.get_attribute('aria-label')
                    # 從 aria-label 解析：「評分：4.1 顆星. 29 評論」
                    if aria_label and '：' in aria_label:
                        parts = aria_label.split('：')[1].split()
                        if parts:
                            rating_text = parts[0]  # "4.1"
                
                rating = float(rating_text) if rating_text and rating_text.replace('.', '').isdigit() else None
                
                # 評論數（從同一個 aria-label 解析）
                review_count = None
                if await rating_elem.count() > 0:
                    aria_label = await rating_elem.get_attribute('aria-label')
                    if aria_label and '評論' in aria_label:
                        # 解析「29 評論」或「320+ 評論」
                        import re
                        match = re.search(r'(\d+\+?)\s*評論', aria_label)
                        if match:
                            review_count = match.group(1)
                
                # ETA（精確選擇器：包含「預估出發時間」）
                eta_elem = card.locator('[aria-label*="預估出發時間"]').first
                eta = None
                if await eta_elem.count() > 0:
                    aria_label = await eta_elem.get_attribute('aria-label')
                    # 從 aria-label 解析：「預估出發時間：31 分鐘」
                    if aria_label and '：' in aria_label:
                        eta = aria_label.split('：')[1]  # "31 分鐘"
                
                # URL（確保有效）
                link_elem = card.locator('a[href*="/store/"]')
                url = await link_elem.get_attribute('href') if await link_elem.count() > 0 else None
                if url:
                    if not url.startswith('http'):
                        url = f"https://www.ubereats.com{url}"
                else:
                    # 沒有 URL 就用首頁
                    url = "https://www.ubereats.com/tw"
                
                # 最終驗證：確保是有效的 https URL
                if not url.startswith('https://'):
                    url = "https://www.ubereats.com/tw"
                
                restaurants.append({
                    "name": name,
                    "rating": rating,
                    "review_count": review_count,
                    "eta": eta,
                    "url": url
                })
                
            except Exception as e:
                print(f"[Worker] Error extracting card {idx}: {e}")
                continue
        
        print(f"[Worker] Found {len(restaurants)} restaurants")
        
    finally:
        # 關閉 context（browser 保持開啟）
        await context.close()
        print(f"[Worker] Context closed")
    
    if not restaurants:
        return {
            'success': False,
            'error': '抱歉，找不到符合需求的餐廳'
        }
    
    # Step 3: 評分排序
    scorer = ScoringEngine()
    scored_restaurants = scorer.score_restaurants(restaurants, intent)
    
    # Step 4: 生成推薦
    recommender = RecommendationGenerator()
    recommendations = recommender.generate_top_recommendations(scored_restaurants, intent, top_n=3)
    
    print(f"[Worker] Top 3: {[r['name'] for r in recommendations]}")
    
    return {
        'success': True,
        'recommendations': recommendations,
        'total_found': len(restaurants),
        'query': user_message
    }

async def background_worker(line_bot_api: LineBotApi):
    """
    Background Worker - 從 Queue 取任務並處理
    使用 async Playwright
    """
    print("[Worker] Background worker started")
    
    while True:
        try:
            # 從 Queue 取任務（blocking）
            task = await task_queue.get()
            
            user_id = task['user_id']
            user_message = task['message']
            
            print(f"[Worker] Got task from user {user_id[:8]}...")
            
            try:
                # 執行搜尋（async）
                result = await search_and_recommend(user_message)
                
                if result['success']:
                    # Debug: 打印 URL
                    print(f"\n[Worker Debug] Recommendations URLs:")
                    for idx, rec in enumerate(result['recommendations'], 1):
                        print(f"  {idx}. {rec.get('name')}: URL='{rec.get('url')}'")
                    
                    # 建立 Flex Message
                    flex_msg = create_recommendations_flex(
                        result['recommendations'],
                        result['query']
                    )
                    
                    # 推送結果給用戶（文字 + Flex Message）
                    line_bot_api.push_message(
                        user_id,
                        [
                            TextSendMessage(text=f"找到 {result['total_found']} 家餐廳！為你推薦 Top 3："),
                            flex_msg
                        ]
                    )
                else:
                    # 推送錯誤訊息
                    line_bot_api.push_message(
                        user_id,
                        TextSendMessage(text=result['error'])
                    )
                
                print(f"[Worker] Task completed, result pushed to user")
                
            except Exception as e:
                print(f"[Worker] Error processing task: {e}")
                import traceback
                traceback.print_exc()
                
                # 推送錯誤訊息
                line_bot_api.push_message(
                    user_id,
                    TextSendMessage(text=f"抱歉，處理時發生錯誤：{str(e)[:100]}")
                )
            
            finally:
                # 標記任務完成
                task_queue.task_done()
                
        except Exception as e:
            print(f"[Worker] Fatal error in background worker: {e}")
            import traceback
            traceback.print_exc()
            await asyncio.sleep(1)  # 避免瘋狂重試
