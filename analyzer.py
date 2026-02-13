#!/usr/bin/env python3
"""
股票分析儀表板 - 整合版
來源: Yang-1688/daily_stock_analysis + OpenClaw
功能: 產生完整的決策儀表板分析
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


# ============ 持股配置 (完整清單) ============
PORTFOLIO = {
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
    "tw_shares": [
        {"code": "2330.TW", "name": "台積電"},
        {"code": "2317.TW", "name": "鴻海"},
        {"code": "2303.TW", "name": "聯電"},
        {"code": "2379.TW", "name": "瑞昱"},
        {"code": "1326.TW", "name": "台化"},
        {"code": "1310.TW", "name": "台苯"}
    ]
}


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
            
            timestamps = result.get('timestamp', [])
            closing = result['indicators']['quote'][0]['close']
            
            if closing and len(closing) >= 2:
                prev_price = closing[-2]
                if current_price != 'N/A' and prev_price:
                    change_pct = ((current_price - prev_price) / prev_price) * 100
                    change_str = f"{change_pct:+.2f}%"
                    return {"price": current_price, "change": change_str, "prev_close": prev_price}
            
            return {"price": current_price, "change": "N/A", "prev_close": "N/A"}
    except Exception as e:
        return {"price": "N/A", "change": "N/A", "prev_close": "N/A"}


def fetch_technical_indicators(symbol: str) -> Dict:
    """獲取技術指標"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=30d"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            result = data['chart']['result'][0]
            closing = result['indicators']['quote'][0]['close']
            volumes = result['indicators']['quote'][0]['volume']
            
            valid_prices = [p for p in closing if p]
            valid_volumes = [v for v in volumes if v]
            
            if not valid_prices:
                return {"ma5": "N/A", "ma10": "N/A", "ma20": "N/A", "avg_volume": "N/A"}
            
            ma5 = sum(valid_prices[-5:]) / min(5, len(valid_prices))
            ma10 = sum(valid_prices[-10:]) / min(10, len(valid_prices))
            ma20 = sum(valid_prices[-20:]) / min(20, len(valid_prices)) if len(valid_prices) >= 20 else ma10
            avg_volume = sum(valid_volumes) / len(valid_volumes) if valid_volumes else 0
            current_price = valid_prices[-1]
            
            # 乖離率
            deviation = ((current_price - ma20) / ma20 * 100) if ma20 != 0 else 0
            
            # 判斷多頭排列
            ma_trend = "多頭排列" if ma5 > ma10 > ma20 else "整理格局"
            
            return {
                "ma5": ma5,
                "ma10": ma10,
                "ma20": ma20,
                "avg_volume": avg_volume,
                "current_price": current_price,
                "deviation": deviation,
                "ma_trend": ma_trend
            }
    except Exception as e:
        return {"ma5": "N/A", "ma10": "N/A", "ma20": "N/A", "avg_volume": "N/A", "error": str(e)}


def get_stock_news(symbol: str, name: str) -> Dict:
    """從 Google News RSS 獲取新聞"""
    try:
        query = f'"{symbol}" OR "{name}" stock'
        encoded = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            content = response.read().decode('utf-8')
            root = ET.fromstring(content)
            items = []
            for item in root.findall('channel/item')[:5]:
                title = item.find('title')
                if title is not None and title.text:
                    items.append(title.text)
            return {"news": items}
    except Exception as e:
        return {"news": []}


def analyze_stock(symbol: str, name: str, market: str = "") -> Dict:
    """完整股票分析"""
    price_data = fetch_stock_price(symbol)
    tech = fetch_technical_indicators(symbol)
    news = get_stock_news(symbol, name)
    
    # 計算評分 (簡化版)
    score = 50  # 基礎分
    checks = []
    
    # 多頭排列
    if tech.get("ma_trend") == "多頭排列":
        score += 15
        checks.append(("多頭排列", True, "MA5 > MA10 > MA20"))
    else:
        checks.append(("多頭排列", False, "整理格局"))
    
    # 乖離率
    deviation = tech.get("deviation", 0)
    if isinstance(deviation, (int, float)):
        if abs(deviation) < 5:
            score += 10
            checks.append(("乖離率<5%", True, f"{deviation:+.1f}%"))
        elif deviation > 8:
            score -= 10
            checks.append(("乖離率<5%", False, f"{deviation:+.1f}% (偏高)"))
        else:
            checks.append(("乖離率<5%", True, f"{deviation:+.1f}% (正常)"))
    else:
        checks.append(("乖離率<5%", None, "數據缺失"))
    
    # 漲跌幅
    change_str = price_data.get("change", "N/A")
    if isinstance(change_str, str) and change_str != "N/A":
        try:
            change_val = float(change_str.replace("%", "").replace("+", ""))
            if change_val > 0:
                score += 5
                checks.append(("股價動能", True, f"+{change_val}%"))
            elif change_val < -3:
                score -= 5
                checks.append(("股價動能", False, f"{change_val}%"))
            else:
                checks.append(("股價動能", True, f"{change_val}%"))
        except:
            pass
    
    # 風險等級
    if score >= 70:
        risk = "🟢 低"
    elif score >= 50:
        risk = "🟡 中"
    else:
        risk = "🔴 高"
    
    # 決策
    if score >= 70:
        decision = "🟢 買入"
    elif score >= 50:
        decision = "🟡 觀望"
    else:
        decision = "🔴 減碼"
    
    # 支撐/壓力位
    current_price = tech.get("current_price")
    if isinstance(current_price, (int, float)):
        support = current_price * 0.95
        resistance = current_price * 1.10
    else:
        support = "N/A"
        resistance = "N/A"
    
    return {
        "symbol": symbol,
        "name": name,
        "market": market,
        "price": price_data.get("price", "N/A"),
        "change": price_data.get("change", "N/A"),
        "score": score,
        "risk": risk,
        "decision": decision,
        "ma5": tech.get("ma5", "N/A"),
        "ma10": tech.get("ma10", "N/A"),
        "ma20": tech.get("ma20", "N/A"),
        "ma_trend": tech.get("ma_trend", "N/A"),
        "deviation": deviation,
        "support": f"{support:.2f}" if isinstance(support, float) else "N/A",
        "resistance": f"{resistance:.2f}" if isinstance(resistance, float) else "N/A",
        "avg_volume": tech.get("avg_volume", "N/A"),
        "checks": checks,
        "news": news.get("news", [])[:3]
    }


def generate_analysis_report(symbol: str, name: str, market: str = "") -> str:
    """產生完整分析報告"""
    result = analyze_stock(symbol, name, market)
    
    report = []
    report.append("=" * 60)
    report.append(f"📊 {result['decision']} | {name} ({result['symbol']})")
    report.append("=" * 60)
    report.append(f"🕐 分析時間: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC")
    report.append("")
    
    report.append(f"📈 **評分**: {result['score']}/100 | 風險: {result['risk']}")
    report.append("")
    
    # 數據透視
    report.append("📊 **數據透視**")
    report.append(f"  • 當前價: {result['price']}")
    report.append(f"  • 漲跌幅: {result['change']}")
    report.append(f"  • MA5: {result['ma5']:.2f}" if isinstance(result['ma5'], float) else f"  • MA5: {result['ma5']}")
    report.append(f"  • MA10: {result['ma10']:.2f}" if isinstance(result['ma10'], float) else f"  • MA10: {result['ma10']}")
    report.append(f"  • MA20: {result['ma20']:.2f}" if isinstance(result['ma20'], float) else f"  • MA20: {result['ma20']}")
    report.append("")
    
    # 檢查清單
    report.append("✅ **檢查清單**")
    for check_name, status, detail in result['checks']:
        if status is True:
            icon = "✅"
        elif status is False:
            icon = "❌"
        else:
            icon = "⚠️"
        report.append(f"  {icon} {check_name}: {detail}")
    report.append("")
    
    # 新聞
    if result['news']:
        report.append("📰 **最新新聞**")
        for i, n in enumerate(result['news'], 1):
            clean_title = re.sub(r'\s+-\s+[A-Za-z]+$', '', n)
            report.append(f"  {i}. {clean_title[:80]}...")
        report.append("")
    
    # 核心結論
    report.append("📌 **核心結論**")
    if result['decision'].startswith("🟢"):
        thesis = f"技術面{result['ma_trend']}，股價動能良好，建議分批布局。"
    elif result['decision'].startswith("🟡"):
        thesis = f"技術面{random.choice(['整理格局','區間震盪'])}，建議觀望或小量試單。"
    else:
        thesis = f"技術面偏弱，建議減碼或停損。"
    
    report.append(f"**一句話決策**: {thesis}")
    report.append("")
    
    # 參考點位
    report.append("💰 **參考點位**")
    report.append(f"  • 狙擊: {result['price']}" if result['price'] != "N/A" else "  • 狙擊: 待計算")
    report.append(f"  • 止損: {result['support']}" if result['support'] != "N/A" else "  • 止損: 待計算")
    report.append(f"  • 目標: {result['resistance']}" if result['resistance'] != "N/A" else "  • 目標: 待計算")
    report.append("")
    
    report.append("=" * 60)
    report.append("🔗 資料來源: Yahoo Finance API + Google News RSS")
    report.append("🤖 分析: OpenClaw + Analyzer v1.0")
    
    return "\n".join(report)


def generate_portfolio_report() -> str:
    """產生持股完整報告"""
    report = []
    report.append("=" * 60)
    report.append("💼 持股決策儀表板 | Portfolio Dashboard")
    report.append(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC")
    report.append("=" * 60)
    
    all_stocks = (
        [(s['code'], s['name'], "美股") for s in PORTFOLIO["us_shares"]] +
        [(s['code'], s['name'], "台股") for s in PORTFOLIO["tw_shares"]] +
        [(s['code'], s['name'], "港股") for s in PORTFOLIO["hk_shares"][:5]] +
        [(s['code'], s['name'], "A股") for s in PORTFOLIO["a_shares"][:5]]
    )
    
    results = []
    for code, name, market in all_stocks:
        try:
            result = analyze_stock(code, name, market)
            results.append(result)
        except Exception as e:
            pass
    
    # 統計
    buy_count = len([r for r in results if r['decision'].startswith("🟢")])
    watch_count = len([r for r in results if r['decision'].startswith("🟡")])
    sell_count = len([r for r in results if r['decision'].startswith("🔴")])
    
    report.append(f"\n**共分析 {len(results)} 只股票** | 🟢買入:{buy_count} 🟡觀望:{watch_count} 🔴賣出:{sell_count}\n")
    
    # 分類顯示
    report.append("-" * 60)
    report.append("🟢 **買入**")
    report.append("-" * 60)
    for r in results:
        if r['decision'].startswith("🟢"):
            report.append(f"\n🔹 {r['name']} ({r['symbol']})")
            report.append(f"   評分: {r['score']}/100 | {r['change']}")
            if r['news']:
                report.append(f"   📰 {r['news'][0][:60]}...")
    
    report.append("\n" + "-" * 60)
    report.append("🟡 **觀望**")
    report.append("-" * 60)
    for r in results:
        if r['decision'].startswith("🟡"):
            report.append(f"\n🔹 {r['name']} ({r['symbol']})")
            report.append(f"   評分: {r['score']}/100 | {r['change']}")
    
    report.append("\n" + "-" * 60)
    report.append("🔴 **減碼**")
    report.append("-" * 60)
    for r in results:
        if r['decision'].startswith("🔴"):
            report.append(f"\n🔹 {r['name']} ({r['symbol']})")
            report.append(f"   評分: {r['score']}/100 | {r['change']}")
    
    report.append("\n" + "=" * 60)
    report.append("🔗 資料來源: Yahoo Finance API + Google News RSS")
    
    return "\n".join(report)


if __name__ == "__main__":
    import sys
    import re
    
    if len(sys.argv) > 2:
        print(generate_analysis_report(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else ""))
    elif len(sys.argv) > 1:
        print(generate_analysis_report(sys.argv[1], sys.argv[1]))
    else:
        print(generate_portfolio_report())
