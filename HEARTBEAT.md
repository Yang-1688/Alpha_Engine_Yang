# 🔐 Juan 快報排程

## ⚠️ SerpApi 狀態
- **狀態：** 已暫停（配額 250 次/月，已用 225 次）
- **替代方案：** Google News RSS

## Cron Jobs (僅 2 項)

| ID | 名稱 | 時間 (UTC+8) | 時區 | Session |
|----|------|-------------|------|---------|
| 1 | Chad 每日財經快報 | 每日 07:30 | Asia/Taipei | main |
| 2 | Chad 持股組合新聞快報 (新版格式) | 每日 19:30 | Asia/Taipei | main |

## Cron 設定

```bash
# 財經快報 - 每天 07:30 (UTC+8)
cron.add({
  name: "Chad 每日財經快報",
  schedule: { kind: "cron", expr: "30 7 * * *", "tz": "Asia/Taipei" },
  payload: { kind: "systemEvent", "text": "..." },
  sessionTarget: "main"
})

# 持股快報 - 每天 19:30 (UTC+8)
cron.add({
  name: "Chad 持股組合新聞快報 (新版格式)",
  schedule: { kind: "cron", expr: "30 19 * * *", "tz": "Asia/Taipei" },
  payload: { kind: "systemEvent", "text": "..." },
  sessionTarget: "main"
})
```

## 快報內容

### 📈 財經快報 (07:30)
- 來源: Google News RSS
- 內容: 美股、港股/A股、台股、加密貨幣、科技趨勢頭條
- 格式: 5 條重點新聞 + 技術分析摘要

### 💼 持股快報 (19:30)
- 來源: Google News RSS + Yahoo Finance API
- 內容: 持股新聞 + 決策儀表板
- 格式: 10 條持股相關新聞 + 標籤分類 (#低PB, #MA趨勢, #轉機 等)

## 技術架構

### 資料來源優先順序
1. efinance (東財爬蟲) - 待安裝
2. akshare (東財/新浪/騰訊) - 待安裝
3. pytdx (通達信) - 待安裝
4. baostock (證券寶) - 待安裝
5. Fallback: Yahoo Finance API + Google News RSS

### 持股標籤分類
- 基本面: #低PB, #高殖利率, #轉機
- 技術面: #MA趨勢, #低基期, #突破
- 主題: #AI概念, #石化, #台塑集團
- 籌碼 (台股): #籌碼健康, #籌碼凌亂
- 風險: #高波動, #流動性低

## 更新日誌
- 2026-02-11: 整合為 2 個 cron jobs，統一使用 main session
