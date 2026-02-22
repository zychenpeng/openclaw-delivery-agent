"""
Scoring Engine - 評分引擎
根據多項因素為餐廳評分並排序
"""
from typing import List, Dict, Optional

class ScoringEngine:
    """餐廳評分引擎"""
    
    # 預設權重（調整後：偏好匹配優先）
    DEFAULT_WEIGHTS = {
        "preference_match": 0.35,  # 偏好匹配度（提高）
        "price_score": 0.20,       # 價格分數
        "eta_score": 0.20,         # 送達時間分數
        "rating_score": 0.15,      # 評分分數
        "popularity": 0.10,        # 熱門度
    }
    
    def __init__(self, weights: Optional[Dict] = None):
        """
        初始化評分引擎
        
        Args:
            weights: 自訂權重，若無則使用預設值
        """
        self.weights = weights or self.DEFAULT_WEIGHTS
    
    def score_restaurants(
        self,
        restaurants: List[Dict],
        intent: Dict,
        menu_data: Optional[Dict] = None
    ) -> List[Dict]:
        """
        為餐廳列表評分並排序
        
        Args:
            restaurants: 搜尋結果列表
            intent: 用戶需求 (from IntentParser)
            menu_data: 可選的菜單資料（含價格資訊）
        
        Returns:
            排序後的餐廳列表（含分數和理由）
        """
        scored = []
        
        for restaurant in restaurants:
            score_detail = self._calculate_score(restaurant, intent, menu_data)
            
            # 加入總分和分項分數
            restaurant["score"] = score_detail["total_score"]
            restaurant["score_detail"] = score_detail
            
            scored.append(restaurant)
        
        # 按總分排序（降序）
        scored.sort(key=lambda x: x["score"], reverse=True)
        
        return scored
    
    def _calculate_score(
        self,
        restaurant: Dict,
        intent: Dict,
        menu_data: Optional[Dict]
    ) -> Dict:
        """計算單一餐廳的分數"""
        
        scores = {}
        
        # 1. 價格分數（預算越符合分數越高）
        scores["price_score"] = self._score_price(restaurant, intent, menu_data)
        
        # 2. ETA 分數（送達時間越短分數越高）
        scores["eta_score"] = self._score_eta(restaurant, intent)
        
        # 3. 評分分數（店家評分越高分數越高）
        scores["rating_score"] = self._score_rating(restaurant)
        
        # 4. 偏好匹配度（符合口味偏好）
        scores["preference_match"] = self._score_preference(restaurant, intent)
        
        # 5. 熱門度（評論數越多分數越高）
        scores["popularity"] = self._score_popularity(restaurant)
        
        # 計算加權總分
        total_score = sum(
            scores[key] * self.weights[key]
            for key in scores.keys()
        )
        
        return {
            "total_score": round(total_score, 2),
            **scores
        }
    
    def _score_price(
        self,
        restaurant: Dict,
        intent: Dict,
        menu_data: Optional[Dict]
    ) -> float:
        """
        價格分數（0-1）
        如果有預算限制，越接近但不超過預算分數越高
        """
        budget = intent.get("budget_max")
        
        if not budget:
            return 0.8  # 無預算限制，給中等分數
        
        # 如果有菜單資料，估算實際價格
        # 這裡簡化：用店名判斷價位（實際應該用菜單平均價格）
        estimated_price = self._estimate_price(restaurant, menu_data)
        
        if estimated_price is None:
            return 0.5  # 無法估算，給中等分數
        
        # 如果超過預算，分數大幅降低
        if estimated_price > budget:
            excess_ratio = (estimated_price - budget) / budget
            return max(0, 1 - excess_ratio * 2)  # 超過越多分數越低
        
        # 在預算內，越接近預算分數越高（充分利用預算）
        ratio = estimated_price / budget
        return ratio  # 0.7-1.0 之間
    
    def _score_eta(self, restaurant: Dict, intent: Dict) -> float:
        """
        ETA 分數（0-1）
        送達時間越短分數越高
        """
        eta_str = restaurant.get("eta")
        eta_limit = intent.get("eta_max")
        
        if not eta_str:
            return 0.5  # 無 ETA 資訊
        
        # 解析 ETA（例如 "25 分鐘"）
        import re
        match = re.search(r'(\d+)', eta_str)
        if not match:
            return 0.5
        
        eta_minutes = int(match.group(1))
        
        # 如果有時間限制
        if eta_limit:
            if eta_minutes > eta_limit:
                # 超過時間限制，分數大幅降低
                excess = (eta_minutes - eta_limit) / eta_limit
                return max(0, 1 - excess * 2)
            else:
                # 在限制內，越快分數越高
                return 1 - (eta_minutes / eta_limit) * 0.5
        
        # 無時間限制，30 分鐘以內為滿分，越長分數越低
        if eta_minutes <= 30:
            return 1.0
        else:
            return max(0, 1 - (eta_minutes - 30) / 60)
    
    def _score_rating(self, restaurant: Dict) -> float:
        """
        評分分數（0-1）
        店家評分越高分數越高
        """
        rating = restaurant.get("rating")
        
        if rating is None:
            return 0.5  # 無評分，給中等分數
        
        # 假設評分是 0-5 分制
        # 4.5 分以上為優秀（0.9-1.0）
        # 4.0-4.5 為良好（0.7-0.9）
        # 3.5-4.0 為普通（0.5-0.7）
        # 3.5 以下較差（< 0.5）
        
        normalized = rating / 5.0
        
        # 提高高分餐廳的優勢
        if rating >= 4.5:
            return min(1.0, normalized + 0.1)
        
        return normalized
    
    def _score_preference(self, restaurant: Dict, intent: Dict) -> float:
        """
        偏好匹配度（0-1）
        店名或菜單是否符合用戶口味偏好
        **不符合偏好的店給予低分（0.2-0.3），符合的給高分（0.9-1.0）**
        """
        preferences = intent.get("preferences", [])
        
        if not preferences:
            return 0.7  # 無偏好，給中等分數
        
        name = restaurant.get("name", "").lower()
        
        # 口味映射（英文 -> 中文關鍵字）
        taste_keywords = {
            "spicy": ["辣", "麻辣", "川", "湘", "韓", "泰", "椒"],
            "light": ["清", "養生", "健康", "蔬", "素"],
            "sweet": ["甜", "dessert", "糖", "蛋糕", "冰"],
        }
        
        # 檢查是否符合偏好
        match_count = 0
        for pref in preferences:
            keywords = taste_keywords.get(pref, [])
            for keyword in keywords:
                if keyword in name:
                    match_count += 1
                    break
        
        # 符合偏好：高分
        if match_count > 0:
            return min(1.0, 0.85 + match_count * 0.15)
        
        # 不符合偏好：大幅降低分數
        # 便利商店、連鎖速食等通用店家給 0.3
        generic_stores = ["便利商店", "全家", "7-11", "萊爾富", "超商"]
        if any(keyword in name for keyword in generic_stores):
            return 0.25
        
        # 其他不符合的店給 0.3
        return 0.3
    
    def _score_popularity(self, restaurant: Dict) -> float:
        """
        熱門度（0-1）
        根據評論數判斷
        """
        review_count_str = restaurant.get("review_count")
        
        if not review_count_str:
            return 0.5  # 無資料
        
        # 解析評論數（例如 "(5,000+)"）
        import re
        match = re.search(r'([\d,]+)', review_count_str)
        if not match:
            return 0.5
        
        count_str = match.group(1).replace(',', '')
        
        try:
            count = int(count_str.replace('+', ''))
        except:
            return 0.5
        
        # 評論數對應分數
        # 1000+ 為熱門（0.8-1.0）
        # 100-1000 為普通（0.5-0.8）
        # <100 為冷門（0.3-0.5）
        
        if count >= 1000:
            return min(1.0, 0.8 + (count - 1000) / 10000)
        elif count >= 100:
            return 0.5 + (count - 100) / 900 * 0.3
        else:
            return 0.3 + count / 100 * 0.2
    
    def _estimate_price(
        self,
        restaurant: Dict,
        menu_data: Optional[Dict]
    ) -> Optional[float]:
        """
        估算餐廳價位
        如果有菜單資料，用平均價格；否則用店名判斷
        """
        # TODO: 實際實作應該用菜單資料計算平均價格
        # 這裡簡化版本：用店名推測
        
        name = restaurant.get("name", "").lower()
        
        # 簡易價位判斷
        if any(kw in name for kw in ["麥當勞", "肯德基", "頂呱呱"]):
            return 150
        elif any(kw in name for kw in ["高級", "精緻", "buffet"]):
            return 500
        elif any(kw in name for kw in ["便當", "小吃", "攤"]):
            return 100
        else:
            return 200  # 預設
