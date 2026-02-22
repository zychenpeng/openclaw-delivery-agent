"""
Intent Parser - 需求解析引擎
將自然語言需求轉換為結構化查詢參數
"""
from typing import Dict, List, Optional
import re

class IntentParser:
    """需求解析器"""
    
    # 關鍵字映射
    MEAL_TYPES = {
        "早餐": "breakfast",
        "午餐": "lunch",
        "晚餐": "dinner",
        "宵夜": "late_night",
        "下午茶": "afternoon_tea",
    }
    
    TASTE_KEYWORDS = {
        "辣": "spicy",
        "麻辣": "spicy",
        "清淡": "light",
        "重口味": "heavy",
        "甜": "sweet",
        "酸": "sour",
        "鹹": "salty",
    }
    
    DIETARY_KEYWORDS = {
        "素食": "vegetarian",
        "素": "vegetarian",
        "清真": "halal",
        "不吃牛": "no_beef",
        "不吃豬": "no_pork",
    }
    
    def parse(self, user_input: str) -> Dict:
        """
        解析用戶輸入
        
        Args:
            user_input: 自然語言需求，例如「宵夜 300 內 要辣 30 分鐘」
        
        Returns:
            {
                "meal_type": str,
                "budget_max": int,
                "preferences": List[str],
                "eta_max": int,
                "dietary_restrictions": List[str],
                "keywords": List[str]  # 搜尋關鍵字
            }
        """
        intent = {
            "meal_type": None,
            "budget_max": None,
            "preferences": [],
            "eta_max": None,
            "dietary_restrictions": [],
            "keywords": [],
        }
        
        # 餐別識別
        for keyword, meal_type in self.MEAL_TYPES.items():
            if keyword in user_input:
                intent["meal_type"] = meal_type
                break
        
        # 預算識別（正則表達式）
        budget_patterns = [
            r'(\d+)\s*[元塊以內之下]',  # 300元內、300以內
            r'(\d+)\s*內',              # 300內
            r'(\d+)\s*以下',            # 300以下
            r'預算\s*(\d+)',            # 預算300
        ]
        
        for pattern in budget_patterns:
            match = re.search(pattern, user_input)
            if match:
                intent["budget_max"] = int(match.group(1))
                break
        
        # 口味偏好識別
        for keyword, taste in self.TASTE_KEYWORDS.items():
            if keyword in user_input:
                if taste not in intent["preferences"]:
                    intent["preferences"].append(taste)
        
        # 飲食限制識別
        for keyword, restriction in self.DIETARY_KEYWORDS.items():
            if keyword in user_input:
                if restriction not in intent["dietary_restrictions"]:
                    intent["dietary_restrictions"].append(restriction)
        
        # ETA 識別（分鐘）
        eta_patterns = [
            r'(\d+)\s*分[鐘鍾]',         # 30分鐘
            r'快\s*一?點',              # 快一點（設為 20 分鐘）
            r'趕時間',                  # 趕時間（設為 15 分鐘）
        ]
        
        for pattern in eta_patterns:
            match = re.search(pattern, user_input)
            if match:
                if pattern == r'快\s*一?點':
                    intent["eta_max"] = 20
                elif pattern == r'趕時間':
                    intent["eta_max"] = 15
                else:
                    intent["eta_max"] = int(match.group(1))
                break
        
        # 提取搜尋關鍵字（去除已識別的結構化資訊）
        # 這裡簡化處理，實際可用 NER 或 LLM
        keywords = self._extract_keywords(user_input, intent)
        intent["keywords"] = keywords
        
        return intent
    
    def _extract_keywords(self, user_input: str, intent: Dict) -> List[str]:
        """
        提取搜尋關鍵字
        移除已識別的結構化資訊，保留核心需求
        """
        # 移除數字、常見詞彙
        cleaned = user_input
        
        # 移除已識別的餐別
        for keyword in self.MEAL_TYPES.keys():
            cleaned = cleaned.replace(keyword, "")
        
        # 移除預算相關
        cleaned = re.sub(r'\d+\s*[元塊以內之下]', '', cleaned)
        cleaned = re.sub(r'\d+\s*內', '', cleaned)
        cleaned = re.sub(r'預算', '', cleaned)
        
        # 移除時間相關
        cleaned = re.sub(r'\d+\s*分[鐘鍾]', '', cleaned)
        cleaned = cleaned.replace('快一點', '')
        cleaned = cleaned.replace('趕時間', '')
        
        # 清理空白
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # 如果有明確的口味詞，保留作為搜尋關鍵字
        keywords = []
        for keyword in self.TASTE_KEYWORDS.keys():
            if keyword in user_input:
                keywords.append(keyword)
        
        # 如果沒有明確關鍵字，用清理後的文字
        if not keywords and cleaned:
            keywords = [cleaned]
        
        # 如果還是沒有，使用餐別作為關鍵字
        if not keywords and intent["meal_type"]:
            keywords = [list(self.MEAL_TYPES.keys())[list(self.MEAL_TYPES.values()).index(intent["meal_type"])]]
        
        return keywords
    
    def to_search_query(self, intent: Dict) -> str:
        """
        將 intent 轉換為搜尋查詢字串
        """
        if intent["keywords"]:
            return intent["keywords"][0]
        
        if intent["meal_type"]:
            # 反查餐別中文
            for cn, en in self.MEAL_TYPES.items():
                if en == intent["meal_type"]:
                    return cn
        
        return "美食"  # 預設
