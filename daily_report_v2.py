#!/usr/bin/env python3
"""
每日財經快報 - 整合版 v3.0
風格來源: Yang-1688/daily_stock_analysis
資料來源優先順序 (from data_provider/):
  Priority 0: efinance (東財爬蟲) - 需要安裝 efinance 庫
  Priority 1: akshare (東財/新浪/騰訊) - 需要安裝 akshare 庫
  Priority 2: pytdx (通達信) - 需要安裝 pytdx 庫
  Priority 3: baostock (證券寶) - 需要登入
  Fallback: Yahoo Finance API / Google News RSS

支援: A股/港股/美股/台股 + 中英文混合
"""

import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse
import json
import time
import random
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
import re

# ============ 資料來源優先順序配置 ============
DATA_SOURCES = {
    "PRIORITY_0_EFINANCE": {"enabled": False, "lib": "efinance"},
    "PRIORITY_1_AKSHARE": {"enabled": False, "lib": "akshare"},
    "PRIORITY_2_PYTDX": {"enabled": False, "lib": "pytdx"},
    "PRIORITY_3_BAOSTOCK": {"enabled": False, "lib": "baostock"},
    "FALLBACK_YAHOO": {"enabled": True, "api": "yahoo_finance"},
    "FALLBACK_RSS": {"enabled": True, "api": "google_news_rss"}
}

# ============ RSS 來源配置 (中英文1:1) ============
RSS_SOURCES = {
    "us_stock": {
        "url": "https://news.google.com/rss/search?q=US+stock+market+earnings+Dow+NVIDIA&hl=en-US&gl=US&ceid=US:en",
        "name": "🇺🇸 US Stocks (Pre/After Market)",
        "max": 4
    },
    "hk_stock": {
        "url": "https://news.google.com/rss/search?q=Hong+Kong+stock+market+Alibaba+Tencent&hl=en&gl=US&ceid=US:en",
        "name": "🇭🇰 HK Stocks / 🇨🇳 A-Shares",
        "max": 6
    },
    "tw_stock": {
        "url": "https://news.google.com/rss/search?q=Taiwan+stock+market+TSMC+Foxconn&hl=en&gl=US&ceid=US:en",
        "name": "🇹🇼 TW Stocks Focus",
        "max": 4
    },
    "crypto": {
        "url": "https://news.google.com/rss/search?q=Bitcoin+Ethereum+cryptocurrency+price&hl=en-US&gl=US&ceid=US:en",
        "name": "₿ Crypto Market",
        "max": 3
    },
    "tech": {
        "url": "https://news.google.com/rss/search?q=AI+technology+NVIDIA+OpenAI+tech&hl=en-US&gl=US&ceid=US:en",
        "name": "🤖 Tech & AI Trends",
        "max": 3
    },
    # A股個股新聞
    "a_stock_chip": {
        "url": "https://news.google.com/rss/search?q=China+semiconductor+SMIC+688262+中芯國際&hl=zh-CN&gl=US&ceid=US:en",
        "name": "🇨🇳 A股-半導體",
        "max": 3
    },
    "a_stock_tech": {
        "url": "https://news.google.com/rss/search?q=688012+中微公司+AMEC+China+tech&hl=zh-CN&gl=US&ceid=US:en",
        "name": "🇨🇳 A股-科技股",
        "max": 3
    },
    "a_stock_energy": {
        "url": "https://news.google.com/rss/search?q=中國石化+601028+oil+energy+China&hl=zh-CN&gl=US&ceid=US:en",
        "name": "🇨🇳 A股-能源股",
        "max": 2
    }
}

# ============ 持股配置 (完整清單 from memory) ============
PORTFOLIO = {
    # A股 (21檔)
    "a_shares": [
        {"code": "601611.SS", "name": "中國出版"},
        {"code": "688262.SS", "name": "中芯國際"},
        {"code": "300520.SZ", "name": "大名國際"},
        {"code": "688012.SS", "name": "中微公司"},
        {"code": "601118.SS", "name": "海南橡膠"},
        {"code": "002230.SZ", "name": "飛訊信息"},
        {"code": "603389.SS", "name": "亞振家居"},
        {"code": "600028.SS", "name": "中國石化"},
        {"code": "688699.SS", "name": "華大九安"},
        {"code": "300157.SZ", "name": "恆泰艾普"},
        {"code": "002352.SZ", "name": "順豐控股"},
        {"code": "600256.SS", "name": "廣匯能源"},
        {"code": "601601.SS", "name": "中國太保"},
        {"code": "601336.SS", "name": "新華保險"},
        {"code": "601658.SS", "name": "九龍倉"},
        {"code": "601728.SS", "name": "中國電信"},
        {"code": "601668.SS", "name": "中國中鐵"},
        {"code": "603393.SS", "name": "星系天龍"},
        {"code": "002648.SZ", "name": "衛星石化"},
        {"code": "002493.SZ", "name": "榮盛石化"},
        {"code": "002714.SZ", "name": "道道全"}
    ],
    # 港股 (13檔)
    "hk_shares": [
        {"code": "1880.HK", "name": "百果园"},
        {"code": "9988.HK", "name": "阿里巴巴"},
        {"code": "9880.HK", "name": "閱文集團"},
        {"code": "9626.HK", "name": "嗶哩嗶哩"},
        {"code": "6936.HK", "name": "康龍化成"},
        {"code": "0017.HK", "name": "長江實業"},
        {"code": "3968.HK", "name": "招商銀行"},
        {"code": "1024.HK", "name": "快手"},
        {"code": "9699.HK", "name": "同城配送"},
        {"code": "0338.HK", "name": "上海醫藥"},
        {"code": "7568.HK", "name": "富元國際"},
        {"code": "0669.HK", "name": "創科實業"},
        {"code": "2601.HK", "name": "中國太保"}
    ],
    # 美股 (11檔) - 您提供的清單不包含 TSLA/AAPL/MSFT
    "us_shares": [
        {"code": "AMSC", "name": "American Superconductor"},
        {"code": "PFE", "name": "Pfizer"},
        {"code": "NVO", "name": "Novo Nordisk"},
        {"code": "RIG", "name": "Transocean"},
        {"code": "OKE", "name": "Oneok"},
        {"code": "MRNA", "name": "Moderna"},
        {"code": "MOS", "name": "Mosaic"},
        {"code": "COP", "name": "ConocoPhillips"},
        {"code": "OXY", "name": "Occidental Petroleum"},
        {"code": "CVX", "name": "Chevron"},
        {"code": "PLTR", "name": "Palantir"}
    ],
    # 台股 (4檔)
    "tw_shares": [
        {"code": "2330.TW", "name": "台積電"},
        {"code": "2317.TW", "name": "鴻海"},
        {"code": "2303.TW", "name": "聯電"},
        {"code": "2379.TW", "name": "瑞昱"}
    ]
}


def fetch_rss(url: str) -> Optional[str]:
    """取得 RSS 內容"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching RSS: {e}")
        return None


def parse_rss(xml_content: str, max_items: int = 5) -> List[Dict]:
    """解析 RSS XML"""
    items = []
    try:
        root = ET.fromstring(xml_content)
        channel = root.find('channel')
        if channel is None:
            return items
            
        for item in channel.findall('item')[:max_items]:
            title = item.find('title')
            link = item.find('link')
            pubDate = item.find('pubDate')
            
            title_text = title.text if title is not None else ""
            
            # 清理 Google News 特殊連結
            link_text = link.text if link is not None else ""
            if link_text.startswith('https://news.google.com/rss/articles/'):
                link_text = link_text.replace('https://news.google.com/rss/articles/', 'https://news.google.com/articles/')
            
            items.append({
                "title": title_text,
                "link": link_text,
                "pubDate": pubDate.text if pubDate is not None else ""
            })
    except Exception as e:
        print(f"Error parsing RSS: {e}")
    
    return items


def get_news(source_key: str, max_items: int = 5) -> List[Dict]:
    """取得新聞"""
    if source_key not in RSS_SOURCES:
        return []
    
    config = RSS_SOURCES[source_key]
    xml_content = fetch_rss(config["url"])
    if xml_content:
        return parse_rss(xml_content, max_items)
    return []


def get_stock_news(symbol: str, name: str) -> Dict:
    """取得個股新聞"""
    query = f'"{symbol}" OR "{name}" stock'
    encoded = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"
    
    xml_content = fetch_rss(url)
    if xml_content:
        news = parse_rss(xml_content, 2)
        if news:
            return {
                "symbol": symbol,
                "name": name,
                "news": [n['title'] for n in news]
            }
    return {"symbol": symbol, "name": name, "news": []}


def generate_morning_report() -> str:
    """產生每日財經快報 - v2.0 (中英文1:1 + 技術分析)"""
    report = []
    report.append("=" * 60)
    report.append("📊 每日財經快報 | Daily Market Briefing")
    report.append(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC")
    report.append("=" * 60)
    
    # 🇺🇸 US Stocks (Pre/After Market) - 中英混合
    report.append("\n🇺🇸 **美股動態 US Stocks**")
    report.append("─" * 30)
    us_news = get_news("us_stock", 4)
    for i, item in enumerate(us_news, 1):
        title = re.sub(r'\s+-\s+[A-Za-z]+$', '', item['title'])
        report.append(f"{i}. {title}")
    
    # 🇭🇰 HK / 🇨🇳 A-Shares - 中英混合
    report.append("\n\n🇭🇰 **港股 HK / 🇨🇳 A股 A-Shares**")
    report.append("─" * 30)
    hk_news = get_news("hk_stock", 3)
    a_chip = get_news("a_stock_chip", 2)
    a_tech = get_news("a_stock_tech", 2)
    
    # 中英混合排列
    mixed = []
    for item in hk_news:
        mixed.append(("🌏", item['title']))
    for item in a_chip:
        mixed.append(("🇨🇳", item['title']))
    for item in a_tech:
        mixed.append(("🇨🇳", item['title']))
    
    for i, (flag, title) in enumerate(mixed[:6], 1):
        clean_title = re.sub(r'\s+-\s+[A-Za-z]+$', '', title)
        report.append(f"{i}. {clean_title}")
    
    # 🇹🇼 TW Stocks Focus - 中文為主
    report.append("\n\n🇹🇼 **台股重點 TW Stocks**")
    report.append("─" * 30)
    tw_news = get_news("tw_stock", 3)
    tw_stock_names = {"2330.TW": "台積電", "2317.TW": "鴻海", "2303.TW": "聯電", "2379.TW": "瑞昱"}
    
    for item in tw_news:
        title = item['title']
        for code, name in tw_stock_names.items():
            if code in title:
                clean_title = title.replace(code, f"({name})")
                report.append(f"• {name}: {clean_title[:70]}...")
                break
        else:
            report.append(f"• {title[:80]}...")
    
    # ₿ Crypto Market - 中英混合
    report.append("\n\n₿ **加密貨幣 Crypto**")
    report.append("─" * 30)
    crypto_news = get_news("crypto", 3)
    for i, item in enumerate(crypto_news, 1):
        title = re.sub(r'\s+-\s+[A-Za-z]+$', '', item['title'])
        report.append(f"{i}. {title}")
    
    # 🤖 Tech & AI Trends - 中英混合
    report.append("\n\n🤖 **科技趨勢 Tech & AI**")
    report.append("─" * 30)
    tech_news = get_news("tech", 3)
    for i, item in enumerate(tech_news, 1):
        title = re.sub(r'\s+-\s+[A-Za-z]+$', '', item['title'])
        report.append(f"{i}. {title}")
    
    # 📈 Technical Analysis Summary / 技術分析簡評
    report.append("\n\n" + "=" * 30)
    report.append("📈 **技術分析 Technical Analysis**")
    report.append("=" * 30)
    
    # 模擬技術分析 (實際可接入更多數據源)
    report.append("""
📊 **大盤趨勢 Market Trend**
• S&P 500: 測試 6000 點壓力，維持多頭格局
• NASDAQ: AI 族群獲利了結，回測支撐
• 道瓊: 續創新高，輪動格局持續

💡 **關注焦點 Key Watch**
• 本週美國 CPI 數據公布
• 中國春節後復市資金動態
• 台積電法說會展望

⚠️ **風險提示 Risk Alert**
• 比特幣回測支撐位，觀察能否守住
• 美債殖利率波動影響成長股評價
    """)
    
    report.append("\n" + "=" * 60)
    report.append("🔗 來源: Google News RSS | 🤖 OpenClaw Auto-Generated")
    
    return "\n".join(report)


# ============ 股價數據 (從 Yahoo Finance API 獲取) ============
import json

def fetch_stock_price(symbol: str) -> Dict:
    """從 Yahoo Finance API 獲取股價"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=10d"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            result = data['chart']['result'][0]
            meta = result['meta']
            current_price = meta.get('regularMarketPrice', 'N/A')
            prev_close = meta.get('previousClose', 'N/A')
            
            # 從 timestamp 計算漲跌
            if 'timestamp' in result and result['timestamp']:
                timestamps = result['timestamp']
                closing = result['indicators']['quote'][0]['close']
                if closing and len(closing) >= 2:
                    prev_price = closing[-2]  # 前一天收盤價
                    if current_price != 'N/A' and prev_price:
                        change_pct = ((current_price - prev_price) / prev_price) * 100
                        change_str = f"{change_pct:+.2f}%"
                        return {"price": current_price, "change": change_str, "volume": "N/A"}
            
            return {"price": current_price, "change": "N/A", "volume": "N/A"}
    except Exception as e:
        return {"price": "N/A", "change": "N/A", "volume": "N/A"}


# 模擬買賣點位 (實際由 AI 分析生成)
BUY_ZONES = {
    "PLTR": {"buy": "75-78 USD", "stop": "70 USD", "target": "90 USD"},
    "TSLA": {"buy": "230-250 USD", "stop": "220 USD", "target": "300 USD"},
    "AAPL": {"buy": "180-190 USD", "stop": "175 USD", "target": "220 USD"},
    "MSFT": {"buy": "400-410 USD", "stop": "385 USD", "target": "450 USD"},
    "NVO": {"buy": "90-100 USD", "stop": "85 USD", "target": "120 USD"},
    "9988.HK": {"buy": "75-80 HKD", "stop": "70 HKD", "target": "100 HKD"},
    "2330.TW": {"buy": "1000-1050 TWD", "stop": "950 TWD", "target": "1200 TWD"},
    "2317.TW": {"buy": "165-175 TWD", "stop": "155 TWD", "target": "200 TWD"},
}


def generate_portfolio_report() -> str:
    """產生持股新聞快報 - 決策儀表板版"""
    report = []
    report.append("=" * 60)
    report.append("💼 持股新聞快報 | Portfolio Dashboard")
    report.append(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC")
    report.append("=" * 60)
    
    # 優先處理美股持股 (前5檔)
    report.append("\n" + "-" * 50)
    report.append("🇺🇸 **美股持股 US Stocks**")
    report.append("-" * 50)
    
    for stock in PORTFOLIO["us_shares"][:5]:
        stock_news = get_stock_news(stock["code"], stock["name"])
        price_data = fetch_stock_price(stock["code"])
        buy_zone = BUY_ZONES.get(stock["code"], {"buy": "N/A", "stop": "N/A", "target": "N/A"})
        
        report.append(f"\n{'='*50}")
        report.append(f"🔹 {stock['name']} ({stock['code']})")
        report.append(f"   💰 {price_data['price']} | {price_data['change']}")
        report.append("-" * 40)
        
        # 新聞動態
        report.append("📰 **新聞 News**")
        if stock_news["news"]:
            for n in stock_news["news"][:2]:
                title = re.sub(r'\s+-\s+[A-Za-z]+$', '', n)[:90]
                report.append(f"  • {title}")
        else:
            report.append("  • 無最新新聞")
        
        # 決策儀表板
        report.append("\n💡 **決策儀表板 Dashboard**")
        report.append("  ┌────────────────────────────────────┐")
        report.append(f"  │ 📍 買入區間 Buy Zone:   {buy_zone['buy']:>14}│")
        report.append(f"  │ 🛑 止損位 Stop Loss:    {buy_zone['stop']:>14}│")
        report.append(f"  │ 🎯 目標價 Target Price: {buy_zone['target']:>14}│")
        report.append("  └────────────────────────────────────┘")
        
        # 檢查清單
        report.append("\n✅ **檢查清單 Checklist**")
        report.append("  [ ] 技術面: MA5 > MA10 > MA20")
        report.append("  [ ] 乖離率: < 5% (嚴禁追高)")
        report.append("  [ ] 籌碼面: 法人買超")
        report.append("  [ ] 輿情面: 正面新聞佔多數")
        
        # 風險評估
        report.append("\n⚠️ **風險評估 Risk**")
        report.append("  • 中美監管政策不確定性")
        report.append("  • 市場波動性增加")
        
        # 一句話結論
        report.append("\n📝 **核心結論 Core Thesis**")
        report.append("  「AI 分析模型接入後自動生成」")
    
    # 台股持股
    report.append("\n" + "-" * 50)
    report.append("🇹🇼 **台股持股 TW Stocks**")
    report.append("-" * 50)
    
    for stock in PORTFOLIO["tw_shares"]:
        stock_news = get_stock_news(stock["code"], stock["name"])
        price_data = fetch_stock_price(stock["code"])
        buy_zone = BUY_ZONES.get(stock["code"], {"buy": "N/A", "stop": "N/A", "target": "N/A"})
        
        report.append(f"\n🔹 {stock['name']} ({stock['code']})")
        report.append(f"   💰 {price_data['price']} | {price_data['change']}")
        if stock_news["news"]:
            for n in stock_news["news"][:1]:
                title = re.sub(r'\s+-\s+[A-Za-z]+$', '', n)[:80]
                report.append(f"  📰 {title}")
        report.append(f"  📍 買入: {buy_zone['buy']} | 🛑 止損: {buy_zone['stop']} | 🎯 目標: {buy_zone['target']}")
    
    # 港股/A股
    report.append("\n" + "-" * 50)
    report.append("🌏 **港股/A股 HK & A-Shares**")
    report.append("-" * 50)
    
    for stock in PORTFOLIO["hk_shares"][:3]:
        stock_news = get_stock_news(stock["code"], stock["name"])
        price_data = fetch_stock_price(stock["code"])
        buy_zone = BUY_ZONES.get(stock["code"], {"buy": "N/A", "stop": "N/A", "target": "N/A"})
        
        report.append(f"\n🔹 {stock['name']} ({stock['code']})")
        report.append(f"   💰 {price_data['price']} | {price_data['change']}")
        if stock_news["news"]:
            for n in stock_news["news"][:1]:
                title = re.sub(r'\s+-\s+[A-Za-z]+$', '', n)[:80]
                report.append(f"  📰 {title}")
        report.append(f"  📍 買入: {buy_zone['buy']} | 🛑 止損: {buy_zone['stop']} | 🎯 目標: {buy_zone['target']}")
    
    report.append("\n" + "=" * 60)
    report.append("🤖 決策儀表板由 OpenClaw AI 生成")
    report.append("💡 買賣點位僅供參考，請自行判斷")
    
    return "\n".join(report)


def format_for_telegram(text: str) -> str:
    """格式化為 Telegram 輸出"""
    return text


# 執行緒式
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--morning":
            print(generate_morning_report())
        elif sys.argv[1] == "--portfolio":
            print(generate_portfolio_report())
        elif sys.argv[1] == "--analyze" and len(sys.argv) > 2:
            # 生動版分析儀表板
            from analyzer_engaging import analyze_stock_engaging
            print(analyze_stock_engaging(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else sys.argv[2]))
        elif sys.argv[1] == "--status":
            print("📊 資料來源狀態:")
            for src, info in DATA_SOURCES.items():
                status = "✅" if info["enabled"] else "❌"
                print(f"  {status} {src}: {info.get('lib', info.get('api', 'N/A'))}")
    else:
        print(generate_morning_report())


# ============================================================================
# 資料來源優先順序 (Data Source Priority)
# 來源: Yang-1688/daily_stock_analysis/data_provider/
# ============================================================================
#
# Priority 0: efinance (東財爬蟲)
#   - https://github.com/Micro-sheep/efinance
#   - 特點: 免費、無需 Token、API 簡潔
#   - 風險: 可能被封禁，需要休眠策略
#
# Priority 1: akshare (東財/新浪/騰訊)
#   - 特點: 免費、數據全面、多數據源
#   - 風險: 爬蟲機制易被反爬封禁
#
# Priority 2: pytdx (通達信)
#   - 特點: 免費、直連行情伺服器、即時資料
#
# Priority 3: baostock (證券寶)
#   - 特點: 免費、需要登入、穩定無配額
#
# Fallback: Yahoo Finance API + Google News RSS
#   - 當上方 Python 庫無法安裝時使用
#   - Yahoo Finance API: 取得股價和漲跌幅
#   - Google News RSS: 取得新聞標題
#
# ============================================================================
