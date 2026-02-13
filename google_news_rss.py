#!/usr/bin/env python3
"""
Google News RSS 整合模組
用於每日財經快報和持股新聞快報

RSS 來源配置:
- finance_stock: 財經市場新聞
- crypto: 加密貨幣新聞
- technology: 科技/AI 新聞
- portfolio: 持股相關新聞 (可自訂關鍵字)
"""

import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse
from datetime import datetime
from typing import List, Dict, Optional
import re

# ============ RSS 來源配置 ============
RSS_SOURCES = {
    "finance_stock": {
        "url": "https://news.google.com/rss/search?q=finance+stock+market&hl=en-US&gl=US&ceid=US:en",
        "name": "財經市場",
        "max_items": 5
    },
    "crypto": {
        "url": "https://news.google.com/rss/search?q=cryptocurrency+bitcoin+ethereum&hl=en-US&gl=US&ceid=US:en",
        "name": "加密貨幣",
        "max_items": 5
    },
    "technology": {
        "url": "https://news.google.com/rss/search?q=technology+AI+tech&hl=en-US&gl=US&ceid=US:en",
        "name": "科技趨勢",
        "max_items": 5
    },
    "a_shares": {
        "url": "https://news.google.com/rss/search?q=China+A+shares+stock+market&hl=en&gl=US&ceid=US:en",
        "name": "A股市場",
        "max_items": 3
    },
    "hk_shares": {
        "url": "https://news.google.com/rss/search?q=Hong+Kong+stock+market&hl=en&gl=US&ceid=US:en",
        "name": "港股市場",
        "max_items": 3
    },
    "us_tech": {
        "url": "https://news.google.com/rss/search?q=US+tech+stocks+AI&hl=en-US&gl=US&ceid=US:en",
        "name": "美國科技",
        "max_items": 5
    }
}

# ============ 持股新聞關鍵字 ============
PORTFOLIO_KEYWORDS = {
    "AMSC": ["AMSC", "American Superconductor"],
    "PFE": ["Pfizer", "PFE stock"],
    "NVO": ["Novo Nordisk", "NVO", "obesity drug"],
    "RIG": ["Transocean", "RIG", "offshore drilling"],
    "OKE": ["Oneok", "OKE", "natural gas"],
    "MRNA": ["Moderna", "MRNA", "mRNA vaccine"],
    "MOS": ["Mosaic", "MOS", "fertilizer"],
    "COP": ["ConocoPhillips", "COP", "oil"],
    "OXY": ["Occidental Petroleum", "OXY"],
    "PLTR": ["Palantir", "PLTR", "AI"],
    "TSLA": ["Tesla", "TSLA", "electric vehicle"],
    "AAPL": ["Apple", "AAPL", "iPhone"],
    "MSFT": ["Microsoft", "MSFT", "AI Copilot"]
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


def parse_rss(xml_content: str) -> List[Dict]:
    """解析 RSS XML"""
    items = []
    try:
        root = ET.fromstring(xml_content)
        channel = root.find('channel')
        if channel is None:
            return items
            
        for item in channel.findall('item')[:10]:  # 最多取 10 條
            title = item.find('title')
            link = item.find('link')
            pubDate = item.find('pubDate')
            description = item.find('description')
            source = item.find('source')
            
            title_text = title.text if title is not None else ""
            
            # 清理描述中的 HTML
            desc_text = ""
            if description is not None and description.text:
                desc_text = re.sub('<[^<]+?>', '', description.text)[:200]
            
            items.append({
                "title": title_text,
                "link": link.text if link is not None else "",
                "pubDate": pubDate.text if pubDate is not None else "",
                "description": desc_text,
                "source_url": source.text if source is not None else ""
            })
    except Exception as e:
        print(f"Error parsing RSS: {e}")
    
    return items


def get_news_by_source(source_key: str) -> List[Dict]:
    """取得指定來源的新聞"""
    if source_key not in RSS_SOURCES:
        return []
    
    config = RSS_SOURCES[source_key]
    xml_content = fetch_rss(config["url"])
    if xml_content:
        items = parse_rss(xml_content)
        return items[:config["max_items"]]
    return []


def get_portfolio_news(symbol: str) -> List[Dict]:
    """取得特定持股的新聞"""
    keywords = PORTFOLIO_KEYWORDS.get(symbol, [symbol])
    query = " OR ".join([f'"{kw}"' for kw in keywords[:2]])
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    
    xml_content = fetch_rss(url)
    if xml_content:
        return parse_rss(xml_content)[:3]
    return []


def format_news_for_report(news_list: List[Dict], source_name: str) -> str:
    """格式化新聞為快報輸出"""
    if not news_list:
        return f"📰 {source_name}: 無最新新聞"
    
    output = [f"\n📰 *{source_name}*\n"]
    for i, item in enumerate(news_list, 1):
        # 清理 Google News 特殊連結
        link = item['link']
        if link.startswith('https://news.google.com/rss/articles/'):
            link = link.replace('https://news.google.com/rss/articles/', 'https://news.google.com/articles/')
        
        output.append(f"{i}. {item['title']}")
        output.append(f"   🔗 {link[:80]}...")
    
    return "\n".join(output)


def generate_morning_report() -> str:
    """產生每日財經快報"""
    report = []
    report.append("=" * 50)
    report.append("📊 每日財經快報")
    report.append(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC")
    report.append("=" * 50)
    
    # 財經市場
    news = get_news_by_source("finance_stock")
    if news:
        report.append(format_news_for_report(news, "財經市場"))
    
    # 加密貨幣
    news = get_news_by_source("crypto")
    if news:
        report.append(format_news_for_report(news, "加密貨幣"))
    
    # 科技趨勢
    news = get_news_by_source("technology")
    if news:
        report.append(format_news_for_report(news, "科技趨勢"))
    
    return "\n".join(report)


def generate_portfolio_report() -> str:
    """產生持股新聞快報"""
    report = []
    report.append("=" * 50)
    report.append("💼 持股新聞快報")
    report.append(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC")
    report.append("=" * 50)
    
    priority_symbols = ["PLTR", "TSLA", "AAPL", "MSFT", "NVO", "PFE"]
    
    for symbol in priority_symbols:
        news = get_portfolio_news(symbol)
        if news:
            report.append(f"\n🔹 {symbol}")
            for i, item in enumerate(news[:2], 1):
                report.append(f"   {i}. {item['title'][:100]}")
    
    return "\n".join(report)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--morning":
            print(generate_morning_report())
        elif sys.argv[1] == "--portfolio":
            print(generate_portfolio_report())
        elif sys.argv[1] == "--source" and len(sys.argv) > 2:
            news = get_news_by_source(sys.argv[2])
            for item in news:
                print(f"- {item['title']}")
    else:
        # 預設顯示所有來源狀態
        print("📡 Google News RSS 狀態檢查")
        print("-" * 30)
        for key, config in RSS_SOURCES.items():
            news = get_news_by_source(key)
            status = "✅" if news else "❌"
            print(f"{status} {config['name']}: {len(news)} 條新聞")
