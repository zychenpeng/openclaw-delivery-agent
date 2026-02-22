# 手動登入設定指南

## 步驟 1: 執行設定腳本

在專案目錄下執行：

```bash
cd C:\Users\johns\.openclaw\workspace-maomao\projects\openclaw-delivery-agent
python setup_profile.py
```

## 步驟 2: 手動登入 Uber Eats

腳本會自動開啟 Chromium 瀏覽器並導航到 Uber Eats 台灣版：

1. **點擊登入按鈕**（通常在右上角）
2. **輸入手機號碼或 Email**
3. **完成 OTP 驗證碼驗證**（會收到簡訊或 Email）
4. **確認登入成功**：看到帳號圖示或名字顯示在右上角
5. **（選用）設定預設外送地址**：可以先設定好常用地址
6. **關閉瀏覽器視窗**

## 步驟 3: 確認 Profile 已建立

關閉瀏覽器後，檢查是否有以下資料夾：

```
openclaw-delivery-agent/
└── chromium_profile/
    ├── Default/
    │   ├── Cookies
    │   ├── Local Storage/
    │   └── ... (其他瀏覽器資料)
    └── ...
```

✅ 如果看到 `chromium_profile` 資料夾，表示設定完成！

## 步驟 4: 繼續開發

設定完成後，回到 OpenClaw 告訴我：

```
已完成登入，繼續開發 01_launch.py
```

---

## 注意事項

### ⚠️ Profile 安全性
- `chromium_profile/` 資料夾包含你的登入 cookies
- **不要** commit 到 Git（已加入 .gitignore）
- **不要** 分享給他人

### 🔄 如何重新登入？
如果 cookies 過期或需要重新登入：
1. 刪除 `chromium_profile/` 資料夾
2. 重新執行 `python setup_profile.py`

### 🌍 關於地址設定
- 在手動登入時可以先設定好常用地址
- 這樣後續腳本就能直接使用該地址
- 如果沒設定，後續腳本會需要程式化設定地址

---

**準備好後，請執行 `python setup_profile.py`！**
