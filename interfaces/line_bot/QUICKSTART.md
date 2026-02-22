# LINE Bot 快速啟動指南

## 1. 設定環境變數

複製 `.env.example` 並填入 LINE Bot 資訊：

```bash
cd openclaw-delivery-agent
cp .env.example .env
```

編輯 `.env`：
```
LINE_CHANNEL_SECRET=你的 Channel Secret
LINE_CHANNEL_ACCESS_TOKEN=你的 Channel Access Token
```

## 2. 安裝依賴

```bash
cd interfaces/line_bot
pip install -r requirements.txt
```

## 3. 啟動 ngrok

開啟新終端機：
```bash
ngrok http 8000
```

複製 ngrok 提供的 HTTPS URL（例如 `https://abc123.ngrok.io`）

## 4. 設定 LINE Webhook URL

前往 LINE Developers Console → Messaging API 頁面：
- Webhook URL: `https://abc123.ngrok.io/webhook`
- 點「Verify」測試連線
- 開啟「Use webhook」

## 5. 啟動 LINE Bot Server

```bash
cd interfaces/line_bot
python app.py
```

看到以下訊息表示啟動成功：
```
Starting server on http://localhost:8000
```

## 6. 測試

1. 用 LINE 掃描 QR Code 加入 Bot 為好友
2. 傳送訊息：「宵夜 300 內 要辣 30 分鐘」
3. Bot 應該回覆推薦餐廳卡片

## 除錯

### 檢查 Server 日誌
終端機會顯示：
```
[Received] User xxx: 宵夜 300 內 要辣
[Intent] Query: 辣, Budget: 300...
[Search] Found 10 restaurants
[Recommendations] Top 3: [...]
[Sent] 2 message(s)
```

### 檢查 ngrok 請求
前往 http://localhost:4040 查看 ngrok 請求記錄

### 常見問題

**Bot 沒回應？**
- 檢查 Webhook URL 是否正確
- 檢查環境變數是否正確
- 查看 Server 日誌是否有錯誤

**推薦結果不合理？**
- 檢查 Intent Parser 解析結果
- 調整 Scorer 權重
