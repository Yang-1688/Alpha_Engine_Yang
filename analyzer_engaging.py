#!/usr/bin/env python3
"""
股票決策儀表板 - 生動版
來源: Yang-1688/daily_stock_analysis + OpenClaw 風格
功能: 產生擬人化、敘事型的股票分析報告
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
        {"code": "300520.SZ", "name": "科大国创"},
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
                return {}
            
            ma5 = sum(valid_prices[-5:]) / min(5, len(valid_prices))
            ma10 = sum(valid_prices[-10:]) / min(10, len(valid_prices))
            ma20 = sum(valid_prices[-20:]) / min(20, len(valid_prices)) if len(valid_prices) >= 20 else ma10
            avg_volume = sum(valid_volumes) / len(valid_volumes) if valid_volumes else 0
            current_price = valid_prices[-1]
            
            deviation = ((current_price - ma20) / ma20 * 100) if ma20 != 0 else 0
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
    except:
        return {}


def get_stock_news(symbol: str, name: str) -> List[str]:
    """從 Google News RSS 獲取新聞標題"""
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
                    clean_title = re.sub(r'\s+-\s+[A-Za-z]+$', '', title.text)
                    items.append(clean_title)
            return items
    except:
        return []


def analyze_stock_engaging(symbol: str, name: str, market: str = "") -> str:
    """
    產生生動型的股票分析報告
    風格: 敘事型、個人化、像是在跟朋友聊天
    """
    price_data = fetch_stock_price(symbol)
    tech = fetch_technical_indicators(symbol)
    news = get_stock_news(symbol, name)
    
    # 計算評分
    score = 50
    checks = []
    
    # 多頭排列
    if tech.get("ma_trend") == "多頭排列":
        score += 20
        checks.append(("趨勢排列", True, "短期均線已形成多頭排列"))
    else:
        checks.append(("趨勢排列", False, f"{tech.get('ma_trend', '整理格局')}"))
    
    # 乖離率
    deviation = tech.get("deviation", 0)
    if abs(deviation) < 5:
        score += 15
        checks.append(("乖離安全", True, f"乖離率僅 {deviation:+.1f}%"))
    elif deviation > 8:
        score -= 10
        checks.append(("乖離安全", False, f"乖離率偏高 {deviation:+.1f}%"))
    else:
        checks.append(("乖離安全", True, f"乖離率 {deviation:+.1f}%"))
    
    # 漲跌幅
    change_str = price_data.get("change", "N/A")
    if isinstance(change_str, str) and change_str != "N/A":
        try:
            change_val = float(change_str.replace("%", "").replace("+", ""))
            if change_val > 3:
                score += 10
                checks.append(("股價動能", True, f"漲幅 {change_val:.1f}%"))
            elif change_val < -3:
                score -= 5
                checks.append(("股價動能", False, f"跌幅 {change_val:.1f}%"))
        except:
            pass
    
    # 決策
    if score >= 75:
        decision = "🟢買入"
    elif score >= 55:
        decision = "🟡觀望"
    else:
        decision = "🔴賣出"
    
    # 支撐/壓力
    current_price = tech.get("current_price")
    if isinstance(current_price, (int, float)):
        sniper = f"${current_price:.2f}"
        stop = f"${current_price * 0.95:.2f}"
        target = f"${current_price * 1.15:.2f}"
    else:
        sniper = "TBD"
        stop = "TBD"
        target = "TBD"
    
    # 產生報告
    report = []
    report.append("=" * 60)
    report.append(f"📊 決策儀表板 | {datetime.now().strftime('%Y-%m-%d')}")
    report.append("=" * 60)
    report.append(f"\n{decision} | {name} ({symbol})")
    report.append("")
    
    # 核心結論 (敘述型)
    if decision.startswith("🟢"):
        core_conclusion = f"""
受惠於基本面改善與技術面轉強，{name} 股價有望延續上漲格局。
近期 {'多頭排列明確' if tech.get('ma_trend') == '多頭排列' else '整理後有望突破'}，建議可分批布局。"""
    elif decision.startswith("🟡"):
        core_conclusion = f"""
{name} 處於整理格局，基本面與技術面暫無明確方向。
建議觀望為主，待突破整理區間後再行介入。"""
    else:
        core_conclusion = f"""
{name} 技術面偏弱，基本面也無明顯支撐。
建議減碼或觀望，等待築底訊號。"""
    
    report.append(f"📌 核心結論：{core_conclusion.strip()}")
    report.append("")
    
    # 參考點位
    report.append(f"💰 參考點位：")
    report.append(f"   狙擊 {sniper} | 止損 {stop} | 目標 {target}")
    report.append("")
    
    # 輿情情報 (如果有新聞)
    if news:
        report.append("✅ 輿情情報：")
        for n in news[:3]:
            report.append(f"  • {n[:50]}...")
        report.append("")
    else:
        report.append("✅ 輿情情報：")
        report.append("  • 暫無重大新聞")
        report.append("")
    
    # 檢查清單
    report.append("✅ 檢查清單：")
    for check_name, status, detail in checks:
        if status is True:
            icon = "✅"
        elif status is False:
            icon = "❌"
        else:
            icon = "⚠️"
        report.append(f"  [{icon}] {check_name}: {detail}")
    report.append("")
    
    # 悄悄話 (個人化結語)
    whispers = {
        "台苯": "這檔股票的走勢非常像系統中定義的「狙擊買點」，跟隨 SM 報價波動非常靈敏。只要報價不墜，這波轉機行情應該還有戲！🌮",
        "台積電": "作為台灣 AI 供應鏈的領頭羊，台積電的每一次法人動作都備受關注。建議持續追蹤法說會展望。🚀",
        "台化": "石化族群近期受惠於油價回升，台化作為龍頭之一，基本面具支撐。可關注 SM 報價走勢。📈",
        "阿里巴巴": "中國電商巨頭的雲端業務加速成長，拆分計畫重啟，市場給予正面反應。需持續關注監管動向。🔍",
        "PLTR": "AI 概念股波動劇烈，建議設好停損紀律。短期漲多後逢回可以布局。💎",
        "NVO": "減肥藥市場競爭加劇，但長期成長動能仍在。建議回測支撐後分批布局。💊",
    }
    
    whisper_key = next((k for k in whispers if k in name), None)
    whisper = whispers.get(whisper_key, f"{name} 的走勢值得持續關注，建議結合作業面與技術面綜合判斷。")
    
    report.append("💬 Juan 的悄悄話：")
    report.append(f"   「{whisper}」")
    report.append("")
    
    report.append("=" * 60)
    report.append(f"生成時間：{datetime.now().strftime('%Y-%m-%d %H:%M')} UTC")
    report.append("數據來源：Yahoo Finance / Google News RSS")
    
    return "\n".join(report)


if __name__ == "__main__":
    import sys
    import re
    
    if len(sys.argv) > 2:
        print(analyze_stock_engaging(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else ""))
    elif len(sys.argv) > 1:
        print(analyze_stock_engaging(sys.argv[1], sys.argv[1]))
    else:
        print("請輸入股票代號和名稱，例如:")
        print("python3 analyzer_engaging.py 1310.TW 台苯")
