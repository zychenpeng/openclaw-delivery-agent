"""
LINE Bot 啟動腳本
自動啟動 ngrok + FastAPI server
"""
import sys
import os
import time
from threading import Thread

# 加入專案路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from pyngrok import ngrok
import uvicorn

def start_ngrok():
    """啟動 ngrok tunnel"""
    print("\n" + "=" * 60)
    print("Starting ngrok tunnel...")
    print("=" * 60)
    
    # 啟動 ngrok（連接到 localhost:8000）
    public_url = ngrok.connect(8000, bind_tls=True)
    
    print(f"\n✅ ngrok tunnel started!")
    print(f"📡 Public URL: {public_url}")
    print("\n" + "=" * 60)
    print("LINE Webhook 設定步驟：")
    print("=" * 60)
    print("1. 前往 LINE Developers Console")
    print("   https://developers.line.biz/console/")
    print("\n2. 選擇你的 Channel → Messaging API")
    print("\n3. 設定 Webhook URL:")
    print(f"   {public_url}/webhook")
    print("\n4. 點「Verify」測試連線")
    print("\n5. 開啟「Use webhook」")
    print("=" * 60)
    
    return public_url

def main():
    """主程式"""
    from interfaces.line_bot.config import LINE_CHANNEL_SECRET, LINE_CHANNEL_ACCESS_TOKEN
    
    print("\n" + "=" * 60)
    print("LINE Bot Startup")
    print("=" * 60)
    
    # 檢查環境變數
    if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN:
        print("\n❌ 錯誤：未設定 LINE Bot 憑證")
        print("請檢查 .env 檔案是否正確設定：")
        print("  LINE_CHANNEL_SECRET")
        print("  LINE_CHANNEL_ACCESS_TOKEN")
        return
    
    print(f"✅ Channel Secret: {LINE_CHANNEL_SECRET[:20]}...")
    print(f"✅ Access Token: {LINE_CHANNEL_ACCESS_TOKEN[:20]}...")
    
    # 啟動 ngrok
    public_url = start_ngrok()
    
    # 等待用戶設定 webhook
    print("\n按 Enter 繼續啟動 FastAPI server...")
    input()
    
    # 啟動 FastAPI server
    print("\n" + "=" * 60)
    print("Starting FastAPI server...")
    print("=" * 60)
    
    from interfaces.line_bot.app import app
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Bot stopped")
        ngrok.kill()
