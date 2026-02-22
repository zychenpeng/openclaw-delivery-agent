# OpenClaw Delivery Agent - 進度報告

**日期：** 2026-02-22  
**開發時間：** 6 小時（00:00 - 05:43）  
**狀態：** Phase 2 完整運作成功 ✅

---

## 專案概述

**產品定位：** 智慧外送推薦 AI（v2.0 方向：推薦 + 比價，非自動下單）

**核心價值：**
- 解決選擇困難：自然語言輸入需求 → AI 推薦 Top 3
- 智慧評分：多因素評分（評分、ETA、價位、口味匹配）
- 即時推送：LINE Bot 介面，10-20 秒回覆

**技術亮點：**
- Queue + Background Worker 架構（避免 webhook 超時）
- async Playwright + storage_state（無多線程衝突）
- 純 Python 評分引擎（無 LLM 成本）

---

## 已完成功能

### Phase 0: PoC 驗證 ✅
- [x] Playwright 瀏覽器自動化
- [x] Uber Eats 搜尋（去重、URL 抓取）
- [x] 菜單抓取（價格、費用）
- [x] 加入購物車 + 結帳流程（PoC 用，v2.0 不使用）

### Phase 1: Brain Layer ✅
- [x] **Intent Parser**：自然語言 → 結構化需求
  - 餐別、預算、口味偏好、ETA、飲食限制
  - 範例：「宵夜 300 內 要辣 30 分鐘」→ 解析為 `{meal_type: late_night, budget_max: 300, preferences: [spicy], eta_max: 30}`
  
- [x] **Scoring Engine**：多因素評分
  - 權重：偏好匹配 35%、價格 20%、ETA 20%、評分 15%、熱門度 10%
  - 不符合偏好大幅扣分（便利商店給 0.25 分）
  
- [x] **Recommender**：推薦理由生成
  - 自動生成理由：「高評分 4.8 分 + 符合辣味需求」

**測試結果：**
- 輸入：「宵夜 300 內 要辣」
- 推薦：麻辣臭豆腐（0.78）、麻辣火少爺（0.71）、林鼎記麻辣鍋（0.71）
- 驗證：正確過濾全家、統一超商（不符合辣味需求）

### Phase 2: LINE Bot ✅
- [x] **FastAPI Webhook Server**
  - ngrok tunnel（開發用）
  - Health check endpoint
  
- [x] **Queue + Background Worker 架構**
  - Webhook 立刻回「🔍 搜尋中...」（避免超時）
  - Background worker 處理搜尋任務
  - 完成後 push_message 推送結果
  
- [x] **async Playwright + storage_state**
  - 匯出 auth_state.json（cookies）
  - 每次任務用 new_context(storage_state) 載入登入狀態
  - 避免 persistent_context 多線程衝突（CIO 建議方案）
  
- [x] **Flex Message 卡片**
  - Carousel 格式（可左右滑動）
  - 內容：TOP 1/2/3、店名、評分、送達、價位、推薦理由
  - 跳轉按鈕（直接開啟 Uber Eats 店家頁面）
  - URL 中文編碼（修復 Invalid URI 錯誤）

**用戶體驗：**
```
用戶輸入：「宵夜 300 內 要辣」
  ↓
立刻收到：「🔍 搜尋中，請稍候 10-20 秒...」
  ↓
10-20 秒後收到：
  - 文字：「找到 15 家餐廳！為你推薦 Top 3：」
  - 3 張推薦卡片（可滑動查看）
  - 點擊按鈕 → 跳轉 Uber Eats
```

---

## 技術架構

### 目錄結構
```
openclaw-delivery-agent/
├── agent/
│   ├── scrapers/
│   │   ├── browser_manager.py         # 瀏覽器管理
│   │   └── ubereats/
│   │       ├── search.py              # 搜尋 + 去重
│   │       └── menu.py                # 菜單抓取
│   └── planner/
│       ├── intent_parser.py           # 需求解析
│       ├── scorer.py                  # 評分引擎
│       └── recommender.py             # 推薦生成
├── interfaces/
│   └── line_bot/
│       ├── app.py                     # FastAPI server
│       ├── worker_v2.py               # Background worker
│       ├── flex_messages.py           # Flex Message 模板
│       └── config.py                  # 配置
├── auth_state.json                    # 登入狀態（cookies）
├── chromium_profile/                  # 瀏覽器 profile（已棄用）
└── results/                           # 測試結果
```

### 技術棧
- **後端：** FastAPI, asyncio, Queue
- **爬蟲：** Playwright (async API)
- **LINE：** line-bot-sdk, Flex Message
- **部署：** ngrok（開發）, VPS（未來）
- **語言：** Python 3.14
- **無 LLM：** 純 Python 邏輯，零 API 成本

### 關鍵設計決策

**1. Queue + Background Worker**
- **問題：** Playwright 搜尋需 10-20 秒，LINE webhook 有 timeout 限制
- **解決：** 
  - Webhook 只負責收訊息並回「搜尋中」
  - Background worker 獨立處理搜尋任務
  - 完成後用 push_message 推送結果

**2. storage_state 取代 persistent_context**
- **問題：** persistent_context 在多線程環境中會衝突
- **解決（CIO 建議）：**
  - 匯出 cookies 到 auth_state.json
  - 每次任務用 new_context(storage_state) 載入
  - Browser 全域只開一次，context 用完即關閉

**3. 偏好匹配優先**
- **權重：** 偏好匹配 35%（最高）
- **邏輯：** 不符合需求的店（例如便利商店）給 0.25 分
- **效果：** 用戶要「辣」，不會推薦全家、統一超商

---

## 待開發功能

### 短期優化（Week 1-2）
- [ ] 位置支援（LINE Location Message）
- [ ] 多平台比價（foodpanda + Uber Eats）
- [ ] 錯誤處理優化（網路失敗、無結果）
- [ ] 歷史紀錄（記住用戶偏好）

### 中期功能（Week 3-4）
- [ ] 收藏功能
- [ ] 定時推薦（「每天中午 11:30 推薦午餐」）
- [ ] 群組支援（朋友群組投票）
- [ ] Web 介面

### 長期方向（開源/產品化）
- [ ] 真正的 LLM 對話（處理複雜需求）
- [ ] 價格追蹤（促銷通知）
- [ ] 多語言支援
- [ ] 官方 API 整合（如果開放）

---

## 技術挑戰與解決

### 挑戰 1：Playwright 與 asyncio 衝突
- **錯誤：** `It looks like you are using Playwright Sync API inside the asyncio loop`
- **解決：** 改用 async Playwright + ThreadPoolExecutor（後改用 storage_state 方案）

### 挑戰 2：persistent_context 多線程問題
- **錯誤：** `Target page, context or browser has been closed`
- **解決：** 採用 CIO 建議的 storage_state 方案

### 挑戰 3：Flex Message URI 驗證
- **錯誤：** `Invalid action URI`
- **原因：** URL 包含未編碼的中文字符（例如 `/store/東方美早午餐/...`）
- **解決：** 用 `urllib.parse.quote()` 編碼 URL

### 挑戰 4：評分不合理
- **問題：** 用戶要「辣」，卻推薦全家便利商店
- **解決：** 提高偏好匹配權重（20% → 35%），不符合需求大幅扣分

---

## 成本分析

### 目前成本（單用戶開發版）
- **Playwright：** 免費（本機執行）
- **LINE Bot：** 免費（每月 500 則推送訊息額度）
- **ngrok：** 免費（開發用，有流量限制）
- **LLM API：** $0（純 Python 邏輯，無 LLM）

**總計：** $0/月

### 未來成本（多用戶產品化）
- **VPS：** $5-20/月（Railway, DigitalOcean）
- **Playwright：** 可能需升級 VPS 記憶體
- **LINE Bot：** 超過 500 則需付費（$0.003/則）
- **LLM API（可選）：** 如用 Claude 處理複雜對話

**預估：** $20-50/月（100-500 用戶）

---

## 風險評估

### 技術風險
1. **Uber Eats 反爬蟲**
   - 風險：中等（目前未被擋）
   - 緩解：storage_state 比 persistent_context 更低調
   - 備案：改用官方 API（如果開放）

2. **LINE Bot ToS**
   - 風險：低（只做推薦，不涉及金流）
   - 注意：不能濫發廣告訊息

3. **擴展性**
   - 風險：中等（Playwright 消耗資源較多）
   - 緩解：用 Queue 控制並發，避免記憶體爆炸

### 產品風險
1. **用戶需求驗證**
   - 目前只有開發者自己使用
   - 建議：邀請 5-10 位朋友測試

2. **競品**
   - Uber Eats / foodpanda 本身也在優化推薦
   - 差異化：多平台比價 + 自然語言輸入

---

## 下一步建議

### 立即執行（今天）
1. ✅ 休息（已工作 6 小時）
2. 等待 CIO 商業企畫書

### 明天（Week 1）
1. 撰寫 README.md
2. 錄製 Demo 影片
3. 邀請朋友測試

### Week 2
1. 多平台比價（foodpanda）
2. 位置支援
3. 錯誤處理優化

### Week 3-4
1. 決定開源策略
2. 準備 Product Hunt 發布
3. 或轉為商業產品

---

## 團隊協作記錄

**開發者：** Sean（毛毛協助）  
**顧問：** CIO（技術架構建議）

**CIO 貢獻：**
- 建議 storage_state 方案（解決 persistent_context 衝突）
- 產品方向建議（v2.0：推薦 + 比價，非自動下單）

**毛毛貢獻：**
- Phase 0-2 完整實作
- 技術問題診斷與解決
- 架構設計與優化

---

## 附錄

### 測試結果範例

**輸入：** 「宵夜 300 內 要辣 30 分鐘」

**Intent 解析：**
```json
{
  "meal_type": "late_night",
  "budget_max": 300,
  "preferences": ["spicy"],
  "eta_max": 30,
  "keywords": ["辣"]
}
```

**搜尋結果：** 15 家餐廳

**Top 3 推薦：**
1. 台北江麻辣臭豆腐（0.78 分）
   - 評分：4.8 分 (5,000+ 評論)
   - 送達：25 分鐘
   - 推薦理由：高評分 4.8分 + 符合辣味需求

2. 麻辣火少爺（0.71 分）
   - 評分：4.5 分 (1,200+ 評論)
   - 送達：30 分鐘
   - 推薦理由：符合辣味需求 + 快速送達

3. 林鼎記麻辣鍋（0.68 分）
   - 評分：4.3 分 (800+ 評論)
   - 送達：35 分鐘
   - 推薦理由：符合辣味需求 + 價格合理

---

**報告完成時間：** 2026-02-22 05:50  
**專案狀態：** Phase 2 完整運作，可進入下一階段開發或開源準備
