# MEMORY - 長期記憶

## 核心配置
- **名稱**: Juan ( taco 🌮 )
- **配置檔案**: `/home/node/.openclaw/moltbot.json` (Docker 環境)
- **溝通偏好**: 繁體中文，溫暖務實，使用儀表板格式呈現股票分析。

## 股票分析系統 (Yang-1688 邏輯)
- **核心指標**: 低 PB、MA 趨勢 (多頭排列)、低基期、有轉機。
- **籌碼結構 (台股)**: 
    - 關注 20 個交易日的變化。
    - **#籌碼凌亂**: 大戶降、散戶升。
    - **#籌碼健康**: 大戶升、散戶降。
    - 參考數據: 玩股網 (Wantgoo)。
- **分析工具**: 實作於 `portfolio-analyzer/`，支援自動標籤與 TradingView 代碼匯出。
- **快報時間**: 07:30 (財經頭條), 19:30 (持股掃描)。

## 開源專案與 GitHub
- **Alpha_Engine_Yang**: 基於 AlphaGPT 的量化回測引擎，支援 Pine Script 匯出。
    - 新增 `tradingview_verifier.py`，支援 Alpha 公式轉 Pine Script (v5)。
    - 已抓取 PLTR, TGT, OXY, 1301.TW, 2317.TW, 2330.TW 近 5 年數據。
- **GitHub 倉庫**: https://github.com/Yang-1688/Alpha_Engine_Yang
    - **同步策略**: 已將全量代碼、數據及 OpenClaw 配置（MEMORY.md, USER.md 等）推送至 GitHub。後續以 GitHub 為開發與資料調用中心。

## 系統與環境
- **Docker 環境**: 套件 (torch, yfinance 等) 在重啟後會丟失，需注意持久化。

## API 狀態
- **SerpApi**: 每月 250 次配額，需謹慎使用。
- **Finnhub**: 已啟用，用於股票即時數據與公司新聞。
- **Google News RSS**: 目前主要的新聞來源。
