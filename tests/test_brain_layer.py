"""
Brain Layer 整合測試
測試完整流程：需求解析 -> 搜尋 -> 評分 -> 推薦
"""
import os
import json
from datetime import datetime
from agent.scrapers.browser_manager import BrowserManager
from agent.scrapers.ubereats.search import UberEatsSearcher
from agent.planner.intent_parser import IntentParser
from agent.planner.scorer import ScoringEngine
from agent.planner.recommender import RecommendationGenerator

# 配置
PROFILE_PATH = os.path.join(os.path.dirname(__file__), "chromium_profile")
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "results")

def test_complete_flow(user_input: str):
    """
    測試完整流程
    
    Args:
        user_input: 用戶需求，例如「宵夜 300 內 要辣 30 分鐘」
    """
    print("=" * 60)
    print(f"User Input: {user_input}")
    print("=" * 60)
    
    # Step 1: 解析需求
    print("\n[Step 1] Parsing intent...")
    parser = IntentParser()
    intent = parser.parse(user_input)
    
    print(f"  Meal Type: {intent['meal_type']}")
    print(f"  Budget Max: ${intent['budget_max']}" if intent['budget_max'] else "  Budget Max: None")
    print(f"  Preferences: {intent['preferences']}")
    print(f"  ETA Max: {intent['eta_max']} min" if intent['eta_max'] else "  ETA Max: None")
    print(f"  Keywords: {intent['keywords']}")
    
    search_query = parser.to_search_query(intent)
    print(f"  Search Query: {search_query}")
    
    # Step 2: 搜尋餐廳
    print(f"\n[Step 2] Searching restaurants...")
    
    with BrowserManager(PROFILE_PATH, headless=False) as context:
        page = context.pages[0] if context.pages else context.new_page()
        searcher = UberEatsSearcher(page)
        
        restaurants = searcher.search(search_query, limit=10)
        print(f"  Found {len(restaurants)} restaurants")
    
    # Step 3: 評分
    print(f"\n[Step 3] Scoring restaurants...")
    scorer = ScoringEngine()
    scored_restaurants = scorer.score_restaurants(restaurants, intent)
    
    print(f"  Top 3 scores:")
    for idx, r in enumerate(scored_restaurants[:3], 1):
        print(f"    {idx}. {r['name']}: {r['score']:.2f}")
    
    # Step 4: 生成推薦
    print(f"\n[Step 4] Generating recommendations...")
    recommender = RecommendationGenerator()
    recommendations = recommender.generate_top_recommendations(scored_restaurants, intent, top_n=3)
    
    # 輸出推薦結果（簡化版，避免 Unicode 問題）
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    
    for idx, rec in enumerate(recommendations, 1):
        print(f"\n[TOP {idx}] Score: {rec['score']:.2f}")
        print(f"  (Full details saved in JSON)")
    
    # 保存結果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_data = {
        "timestamp": timestamp,
        "user_input": user_input,
        "intent": intent,
        "search_query": search_query,
        "total_found": len(restaurants),
        "recommendations": recommendations
    }
    
    output_path = os.path.join(RESULTS_PATH, f"brain_test_{timestamp}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n[Saved] {output_path}")
    print("=" * 60)
    
    return recommendations

if __name__ == "__main__":
    print("\nTesting Brain Layer - Complete Flow\n")
    
    # 測試案例
    test_cases = [
        "宵夜 300 內 要辣 30 分鐘",
        # "午餐 150 以內 清淡",
        # "早餐 素食 100 內",
    ]
    
    for test_input in test_cases:
        try:
            test_complete_flow(test_input)
            print("\n")
        except Exception as e:
            print(f"\n[ERROR] Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n[OK] Brain Layer Test Complete")
