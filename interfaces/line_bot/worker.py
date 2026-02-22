"""
Background Worker - 獨立處理搜尋任務
使用 asyncio.Queue 實現 producer-consumer pattern
Playwright 在此單線程順序執行，避免多線程衝突
"""
import asyncio
import os
from linebot import LineBotApi
from linebot.models import TextSendMessage
from playwright.sync_api import sync_playwright

# 導入 agent 模組
from agent.planner.intent_parser import IntentParser
from agent.planner.scorer import ScoringEngine
from agent.planner.recommender import RecommendationGenerator
from agent.scrapers.ubereats.search import UberEatsSearcher

# 配置
PROFILE_PATH = os.path.join(os.path.dirname(__file__), "../../chromium_profile")

# 全域 Queue（producer-consumer）
task_queue = asyncio.Queue()

def _search_and_recommend(user_message: str):
    """
    同步函數：執行搜尋 + 評分 + 推薦
    在 background worker 中調用，單線程執行
    """
    print(f"\n[Worker] Processing task: {user_message}")
    
    # Step 1: 解析需求
    parser = IntentParser()
    intent = parser.parse(user_message)
    search_query = parser.to_search_query(intent)
    
    print(f"[Worker] Intent parsed: {search_query}")
    
    # Step 2: 搜尋餐廳（Playwright 在此執行）
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        try:
            if browser.pages:
                page = browser.pages[0]
            else:
                page = browser.new_page()
            
            searcher = UberEatsSearcher(page)
            restaurants = searcher.search(search_query, limit=15)
            
            print(f"[Worker] Found {len(restaurants)} restaurants")
            
        finally:
            browser.close()
    
    if not restaurants:
        return "抱歉，找不到符合需求的餐廳 😢"
    
    # Step 3: 評分排序
    scorer = ScoringEngine()
    scored_restaurants = scorer.score_restaurants(restaurants, intent)
    
    # Step 4: 生成推薦
    recommender = RecommendationGenerator()
    recommendations = recommender.generate_top_recommendations(scored_restaurants, intent, top_n=3)
    
    print(f"[Worker] Top 3: {[r['name'] for r in recommendations]}")
    
    # Step 5: 格式化結果（純文字）
    result_text = f"✅ 找到 {len(restaurants)} 家餐廳！為你推薦 Top 3：\n\n"
    
    for rec in recommendations:
        result_text += f"{rec['rank']}. {rec['name']}\n"
        result_text += f"   評分：{rec['rating']}\n"
        result_text += f"   送達：{rec['eta']}\n"
        result_text += f"   價位：{rec['price_estimate']}\n"
        result_text += f"   {rec['reason'].split('推薦理由：')[1] if '推薦理由：' in rec['reason'] else rec['reason']}\n"
        if rec.get('url'):
            result_text += f"   連結：{rec['url'][:60]}...\n"
        result_text += "\n"
    
    return result_text

async def background_worker(line_bot_api: LineBotApi):
    """
    Background Worker - 從 Queue 取任務並處理
    
    Args:
        line_bot_api: LINE Bot API 實例（用於 push_message）
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
                # 在 executor 中執行同步搜尋函數（避免阻塞 event loop）
                loop = asyncio.get_event_loop()
                result_text = await loop.run_in_executor(
                    None,  # 使用預設 ThreadPoolExecutor
                    _search_and_recommend,
                    user_message
                )
                
                # 推送結果給用戶
                line_bot_api.push_message(
                    user_id,
                    TextSendMessage(text=result_text)
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
