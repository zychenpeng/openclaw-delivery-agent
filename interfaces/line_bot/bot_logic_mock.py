"""
LINE Bot 對話邏輯 - Mock 版本（純文字測試）
用於測試 LINE Bot 基本流程
"""
from linebot.models import TextSendMessage

def handle_text_message(user_message: str, user_id: str):
    """
    處理用戶文字訊息（Mock 版本 - 純文字）
    """
    print(f"[Mock] Processing: {user_message}")
    
    # 簡單文字回覆
    reply_text = """🤖 測試模式運作中！

你傳送了：{msg}

推薦結果（Mock）：
1. 台北江麻辣臭豆腐 - 4.8分
2. 麻辣火少爺 - 4.5分
3. 林鼎記麻辣鍋 - 4.3分

✅ LINE Bot 基本流程正常！
""".format(msg=user_message)
    
    # 回傳純文字訊息
    return [TextSendMessage(text=reply_text)]
