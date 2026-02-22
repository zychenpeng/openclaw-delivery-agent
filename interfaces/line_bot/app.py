"""
LINE Bot Webhook Server (FastAPI)
使用 Queue + Background Worker 架構
Webhook 只負責收訊息並回「搜尋中」，不執行 Playwright
Background Worker 獨立處理搜尋任務，完成後 push_message 回傳
"""
import sys
import os
import asyncio

# 加入專案路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import uvicorn

from interfaces.line_bot.config import LINE_CHANNEL_SECRET, LINE_CHANNEL_ACCESS_TOKEN
# 使用 V2 worker（async Playwright + storage_state）
from interfaces.line_bot.worker_v2 import task_queue, background_worker, init_browser, close_browser

# FastAPI app
app = FastAPI(title="外送推薦 LINE Bot")

# LINE Bot API
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Background worker task（啟動後會一直運行）
worker_task = None

@app.on_event("startup")
async def startup_event():
    """啟動時執行：初始化 browser + 啟動 background worker"""
    global worker_task
    
    print("\n[Startup] Initializing global browser...")
    await init_browser()
    
    print("[Startup] Starting background worker...")
    worker_task = asyncio.create_task(background_worker(line_bot_api))
    print("[Startup] Background worker started")

@app.on_event("shutdown")
async def shutdown_event():
    """關閉時執行：停止 background worker + 關閉 browser"""
    global worker_task
    
    if worker_task:
        print("\n[Shutdown] Stopping background worker...")
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass
        print("[Shutdown] Background worker stopped")
    
    print("[Shutdown] Closing global browser...")
    await close_browser()
    print("[Shutdown] Shutdown complete")

@app.get("/")
def health_check():
    """健康檢查"""
    return {
        "status": "ok",
        "service": "LINE Bot Webhook",
        "queue_size": task_queue.qsize()
    }

@app.post("/webhook")
async def webhook(request: Request):
    """LINE Bot Webhook 端點"""
    # 取得請求內容
    body = await request.body()
    signature = request.headers.get("X-Line-Signature", "")
    
    # 驗證簽名
    try:
        handler.handle(body.decode(), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """
    處理文字訊息（Producer）
    收到訊息 → 放入 Queue → 立刻回「搜尋中」
    """
    user_message = event.message.text
    user_id = event.source.user_id
    
    print(f"\n[Webhook] Received from user {user_id[:8]}...: {user_message}")
    
    try:
        # 放入任務 Queue（non-blocking）
        asyncio.create_task(task_queue.put({
            'user_id': user_id,
            'message': user_message
        }))
        
        print(f"[Webhook] Task queued, queue size: {task_queue.qsize()}")
        
        # 立刻回覆「搜尋中」
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="🔍 搜尋中，請稍候 10-20 秒...")
        )
        
        print(f"[Webhook] Replied '搜尋中', waiting for worker")
        
    except Exception as e:
        print(f"[Webhook Error] {e}")
        import traceback
        traceback.print_exc()
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"抱歉，發生錯誤：{str(e)[:100]}")
        )

if __name__ == "__main__":
    print("=" * 60)
    print("LINE Bot Webhook Server")
    print("=" * 60)
    print(f"Channel Secret: {LINE_CHANNEL_SECRET[:20]}...")
    print(f"Access Token: {LINE_CHANNEL_ACCESS_TOKEN[:20]}...")
    print("=" * 60)
    print("\nStarting server on http://localhost:8000")
    print("Use ngrok: ngrok http 8000")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
