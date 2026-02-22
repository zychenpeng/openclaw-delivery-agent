"""
Recommendation Generator - 推薦理由生成器
根據評分結果生成自然語言推薦理由
"""
from typing import Dict, List
from urllib.parse import quote

class RecommendationGenerator:
    """推薦理由生成器"""
    
    def generate_recommendation(
        self,
        restaurant: Dict,
        intent: Dict,
        rank: int = 1
    ) -> str:
        """
        生成推薦理由
        
        Args:
            restaurant: 餐廳資料（含 score_detail）
            intent: 用戶需求
            rank: 排名（1, 2, 3...）
        
        Returns:
            推薦理由文字
        """
        reasons = []
        score_detail = restaurant.get("score_detail", {})
        
        # 根據各項分數生成理由
        
        # 1. 評分優秀
        if score_detail.get("rating_score", 0) >= 0.9:
            rating = restaurant.get("rating")
            review_count = restaurant.get("review_count", "")
            reasons.append(f"高評分 {rating}分")
        
        # 2. 送達快速
        if score_detail.get("eta_score", 0) >= 0.8:
            eta = restaurant.get("eta", "")
            reasons.append(f"快速送達 ({eta})")
        
        # 3. 符合口味偏好
        if score_detail.get("preference_match", 0) >= 0.8:
            preferences = intent.get("preferences", [])
            if "spicy" in preferences:
                reasons.append("符合辣味需求")
            elif "light" in preferences:
                reasons.append("符合清淡口味")
        
        # 4. 價格合理
        if score_detail.get("price_score", 0) >= 0.7:
            budget = intent.get("budget_max")
            if budget:
                reasons.append(f"符合預算 (${budget}內)")
            else:
                reasons.append("價格合理")
        
        # 5. 熱門店家
        if score_detail.get("popularity", 0) >= 0.8:
            reasons.append("熱門店家")
        
        # 組合理由
        if not reasons:
            # 如果沒有特別突出的優勢，給予通用理由
            reasons = ["綜合表現良好"]
        
        # 根據排名選擇標記（避免 Windows console emoji 問題）
        rank_marker = {
            1: "[TOP 1]",
            2: "[TOP 2]",
            3: "[TOP 3]",
        }
        
        emoji = rank_marker.get(rank, f"[#{rank}]")
        
        reason_text = " + ".join(reasons)
        
        return f"{emoji} 推薦理由：{reason_text}"
    
    def format_recommendation_card(
        self,
        restaurant: Dict,
        intent: Dict,
        rank: int = 1
    ) -> Dict:
        """
        格式化為推薦卡片（LINE Flex Message 用）
        
        Returns:
            {
                "rank": int,
                "name": str,
                "rating": str,
                "eta": str,
                "price_estimate": str,
                "reason": str,
                "url": str
            }
        """
        reason = self.generate_recommendation(restaurant, intent, rank)
        
        rating = restaurant.get("rating")
        review_count = restaurant.get("review_count", "")
        rating_text = f"⭐ {rating}" if rating else "評分未知"
        if review_count:
            rating_text += f" ({review_count})"
        
        eta = restaurant.get("eta", "未知")
        
        # 估算價格（簡化版本）
        price_estimate = self._estimate_display_price(restaurant, intent)
        
        # URL（確保有效 + 編碼中文字符）
        url = restaurant.get("url")
        if not url or not isinstance(url, str) or not url.startswith("http"):
            url = "https://www.ubereats.com/tw"
        else:
            # URL encode 中文字符
            if '/store/' in url:
                parts = url.split('/store/')
                if len(parts) == 2:
                    base = parts[0] + '/store/'
                    path = parts[1]
                    encoded_path = quote(path, safe='/')
                    url = base + encoded_path
        
        return {
            "rank": rank,
            "name": restaurant.get("name", "未知店家"),
            "rating": rating_text,
            "eta": f"⏱ {eta}",
            "price_estimate": price_estimate,
            "reason": reason,
            "url": url,
            "score": restaurant.get("score", 0)
        }
    
    def _estimate_display_price(self, restaurant: Dict, intent: Dict) -> str:
        """估算顯示價格"""
        # 簡化版本：用固定範圍
        name = restaurant.get("name", "").lower()
        
        if any(kw in name for kw in ["麥當勞", "肯德基"]):
            return "約$100-200"
        elif any(kw in name for kw in ["小吃", "便當"]):
            return "約$80-150"
        elif any(kw in name for kw in ["高級", "精緻"]):
            return "約$300-500"
        else:
            return "約$150-250"
    
    def generate_top_recommendations(
        self,
        scored_restaurants: List[Dict],
        intent: Dict,
        top_n: int = 3
    ) -> List[Dict]:
        """
        生成 Top N 推薦列表
        
        Returns:
            List of recommendation cards
        """
        recommendations = []
        
        for idx, restaurant in enumerate(scored_restaurants[:top_n], 1):
            card = self.format_recommendation_card(restaurant, intent, rank=idx)
            recommendations.append(card)
        
        return recommendations
