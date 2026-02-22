"""
LINE Flex Message 模板
用於顯示推薦餐廳卡片
"""
from linebot.models import FlexSendMessage
from urllib.parse import quote

def create_recommendations_flex(recommendations, user_query):
    """
    建立推薦餐廳的 Flex Message（Carousel 格式）
    
    Args:
        recommendations: List of recommendation cards
        user_query: 用戶原始需求
    
    Returns:
        FlexSendMessage
    """
    # 建立每個推薦的 bubble
    bubbles = []
    
    for rec in recommendations:
        bubble = create_restaurant_bubble(rec)
        bubbles.append(bubble)
    
    # Carousel container
    carousel = {
        "type": "carousel",
        "contents": bubbles
    }
    
    return FlexSendMessage(
        alt_text=f"為你找到 {len(recommendations)} 家推薦餐廳",
        contents=carousel
    )

def create_restaurant_bubble(rec):
    """
    建立單一餐廳的 Flex Bubble
    
    Args:
        rec: Recommendation card dict
    
    Returns:
        Flex Bubble dict
    """
    # 排名標記（避免 emoji 問題）
    rank = rec['rank']
    rank_text = f"TOP {rank}"
    
    # 提取推薦理由（去掉 [TOP X] 前綴）
    reason = rec.get('reason', '推薦店家')
    if '] ' in reason:
        reason = reason.split('] ', 1)[1]
    if '推薦理由：' in reason:
        reason = reason.split('推薦理由：')[1]
    
    # 安全取得資料
    name = rec.get('name', '未知店家')
    rating = rec.get('rating', '評分未知')
    eta = rec.get('eta', '未知')
    price = rec.get('price_estimate', '約$150-250')
    url = rec.get('url')
    
    # URL 驗證 + 編碼中文字符
    if not url or not isinstance(url, str) or not url.startswith('https://'):
        url = 'https://www.ubereats.com/tw'
    else:
        # URL encode 中文字符（LINE 要求）
        # 分解 URL: https://domain/path
        if '/store/' in url:
            parts = url.split('/store/')
            if len(parts) == 2:
                base = parts[0] + '/store/'
                path = parts[1]
                # 只編碼路徑部分，保留 / 不編碼
                encoded_path = quote(path, safe='/')
                url = base + encoded_path
    
    # 清理 emoji
    if isinstance(rating, str):
        rating = rating.replace('⭐', '').strip()
    if isinstance(eta, str):
        eta = eta.replace('⏱', '').strip()
    
    # 決定顏色
    colors = {1: "#FF6B35", 2: "#FFA500", 3: "#FFD700"}
    header_color = colors.get(rank, "#999999")
    
    bubble = {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": rank_text,
                    "weight": "bold",
                    "color": "#FFFFFF",
                    "size": "sm"
                }
            ],
            "backgroundColor": header_color
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": name,
                    "weight": "bold",
                    "size": "lg",
                    "wrap": True
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "md",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "baseline",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "評分",
                                    "color": "#AAAAAA",
                                    "size": "sm",
                                    "flex": 2
                                },
                                {
                                    "type": "text",
                                    "text": str(rating),
                                    "wrap": True,
                                    "color": "#666666",
                                    "size": "sm",
                                    "flex": 5
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "baseline",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "送達",
                                    "color": "#AAAAAA",
                                    "size": "sm",
                                    "flex": 2
                                },
                                {
                                    "type": "text",
                                    "text": str(eta),
                                    "wrap": True,
                                    "color": "#666666",
                                    "size": "sm",
                                    "flex": 5
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "baseline",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "價位",
                                    "color": "#AAAAAA",
                                    "size": "sm",
                                    "flex": 2
                                },
                                {
                                    "type": "text",
                                    "text": str(price),
                                    "wrap": True,
                                    "color": "#666666",
                                    "size": "sm",
                                    "flex": 5
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "separator",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": str(reason),
                    "wrap": True,
                    "color": "#666666",
                    "size": "xs",
                    "margin": "md"
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "height": "sm",
                    "action": {
                        "type": "uri",
                        "label": "打開 Uber Eats",
                        "uri": url
                    }
                }
            ],
            "flex": 0
        }
    }
    
    return bubble
