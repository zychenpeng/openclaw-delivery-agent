"""
LINE Bot 配置
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 載入 .env 檔案
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# LINE Bot 設定（從環境變數讀取）
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")

# 本機測試用（正式環境用 ngrok）
WEBHOOK_URL_BASE = os.getenv("WEBHOOK_URL_BASE", "http://localhost:8000")
