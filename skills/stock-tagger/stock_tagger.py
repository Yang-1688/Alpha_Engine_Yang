#!/usr/bin/env python3
"""
股票標籤分類器 | Stock Tagger
來源: Yang-1688/daily_stock_analysis 風格
功能: 為股票加上多維度標籤，便於篩選

使用方法:
    from skills.stock_tagger import StockTagger
    tags = tagger.get_stock_tags("1310.TW", "台苯", market="台股")
    
整合籌碼分析 (台股限定):
    from skills.stock_tagger.chip_analyzer import ChipAnalyzer
    chip = analyzer.analyze_chip("2330.TW", "台積電")
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass

# 引入籌碼分析器
try:
    from .chip_analyzer import ChipAnalyzer, get_chip_tag_for_stock
    CHIP_ANALYZER_AVAILABLE = True
except ImportError:
    CHIP_ANALYZER_AVAILABLE = False


# ============ 標籤定義 ============
TAGS = {
    # 基本面標籤
    "low_pb": {"name": "#低PB", "category": "基本面", "desc": "股價淨值比偏低", "threshold": 1.5},
    "high_yield": {"name": "#高殖利率", "category": "基本面", "desc": "殖利率 > 4%", "threshold": 4.0},
    "low_pe": {"name": "#低PE", "category": "基本面", "desc": "本益比偏低", "threshold": 15.0},
    "turnaround": {"name": "#轉機", "category": "基本面", "desc": "營運谷底反彈", "threshold": 20.0},
    
    # 技術面標籤
    "ma_trend": {"name": "#MA趨勢", "category": "技術面", "desc": "均線多頭排列", "condition": "MA5 > MA10 > MA20"},
    "low_base": {"name": "#低基期", "category": "技術面", "desc": "股價低於MA20 > 5%", "threshold": 0.95},
    "breakout": {"name": "#突破", "category": "技術面", "desc": "放量突破壓力", "condition": "Volume > Avg * 1.5"},
    "strong": {"name": "#強勢", "category": "技術面", "desc": "單日漲幅 > 5%", "threshold": 5.0},
    
    # 主題標籤
    "ai_concept": {"name": "#AI概念", "category": "主題", "desc": "與AI相關", "keywords": ["AI", "人工智慧", "半導體", "晶片"]},
    "green_energy": {"name": "#綠能", "category": "主題", "desc": "環保/新能源", "keywords": ["太陽能", "風電", "電動車", "綠能"]},
    "china_growth": {"name": "#中國成長", "category": "主題", "desc": "受惠中國經濟", "keywords": ["中國", "A股", "中概"]},
    "us_infra": {"name": "#美國基建", "category": "主題", "desc": "受惠基建政策", "keywords": ["基建", "鋼鐵", "水泥"]},
    "petrochemical": {"name": "#石化", "category": "主題", "desc": "石化產業", "keywords": ["石化", "SM", "苯乙烯", "塑化"]},
    "tw_petro": {"name": "#台塑集團", "category": "主題", "desc": "台塑集團相關", "keywords": ["台塑", "台化", "台苯", "南亞", "福懋"]},
    
    # ⚠️ 籌碼標籤 (台股限定)
    "chip_healthy": {"name": "#籌碼健康", "category": "籌碼", "desc": "大戶上升+散戶下降", "chip_tag": "#籌碼健康"},
    "chip_messy": {"name": "#籌碼凌亂", "category": "籌碼", "desc": "大戶下降+散戶上升", "chip_tag": "#籌碼凌亂"},
    "chip_neutral": {"name": "#籌碼中性", "category": "籌碼", "desc": "變化不大", "chip_tag": "#籌碼中性"},
    "chip_concentrated": {"name": "#籌碼集中", "category": "籌碼", "desc": "大戶持股增加", "chip_tag": "#籌碼集中"},
    "chip_dispersed": {"name": "#籌碼分散", "category": "籌碼", "desc": "散戶持股增加", "chip_tag": "#籌碼分散"},
    
    # 風險標籤
    "high_vol": {"name": "#高波動", "category": "風險", "desc": "波動率 > 30%", "threshold": 30.0},
    "low_liquidity": {"name": "#流動性低", "category": "風險", "desc": "成交量 < 1M", "threshold": 1000000},
}

# ============ 持股標籤配置 ============
# 為持股預先定義標籤 (可由分析自動更新)
PORTFOLIO_TAGS = {
    # 台股
    "2330.TW": ["#AI概念", "#MA趨勢", "#高市值"],
    "1310.TW": ["#石化", "#低基期", "#轉機"],
    "1326.TW": ["#石化", "#台塑集團", "#低PB"],
    
    # 美股
    "PLTR": ["#AI概念", "#MA趨勢", "#高成長"],
    "TSLA": ["#AI概念", "#綠能", "#高波動"],
    "NVO": ["#醫藥", "#轉機", "#高殖利率"],
    "PFE": ["#醫藥", "#高殖利率", "#低PE"],
    "AMSC": ["#綠能", "#低基期", "#轉機"],
    
    # 港股
    "9988.HK": ["#中國成長", "#電商", "#轉機"],
    "1880.HK": ["#消費", "#低基期", "#轉機"],
    
    # A股
    "688262.SS": ["#半導體", "#AI概念", "#中國成長"],
    "688012.SS": ["#半導體", "#低基期", "#轉機"],
    "600028.SS": ["#石化", "#國企", "#低PB"],
}


@dataclass
class StockTag:
    """股票標籤"""
    tag: str
    category: str
    score: float  # 0-100
    evidence: str  # 佐證數據


class StockTagger:
    """股票標籤分類器"""
    
    def __init__(self):
        self.tags = TAGS
        self.portfolio_tags = PORTFOLIO_TAGS
    
    def get_stock_tags(self, symbol: str, name: str, market: str = "",
                       price_data: Dict = None, tech_data: Dict = None) -> List[StockTag]:
        """
        為股票產生標籤
        
        Args:
            symbol: 股票代號
            name: 股票名稱
            market: 市場 (台股/美股/港股/A股)
            price_data: 價格數據 {'price': float, 'change': float}
            tech_data: 技術數據 {'ma5': float, 'ma10': float, 'ma20': float, 'volume': float}
        
        Returns:
            List[StockTag]: 標籤列表
        """
        tags = []
        
        # 1. 檢查預設標籤
        if symbol in self.portfolio_tags:
            for tag_key in self.portfolio_tags[symbol]:
                for key, info in self.tags.items():
                    if info["name"] == tag_key:
                        tags.append(StockTag(
                            tag=tag_key,
                            category=info["category"],
                            score=80.0,
                            evidence=f"預設標籤: {info['desc']}"
                        ))
        
        # 2. 根據技術數據添加標籤
        if tech_data:
            ma5 = tech_data.get("ma5", 0)
            ma10 = tech_data.get("ma10", 0)
            ma20 = tech_data.get("ma20", 0)
            price = tech_data.get("price", 0)
            volume = tech_data.get("volume", 0)
            
            # #MA趨勢
            if ma5 > ma10 > ma20:
                tags.append(StockTag(
                    tag="#MA趨勢",
                    category="技術面",
                    score=85.0,
                    evidence=f"MA5({ma5:.2f}) > MA10({ma10:.2f}) > MA20({ma20:.2f})"
                ))
            
            # #低基期
            if ma20 > 0 and price < ma20 * 0.95:
                deviation = (ma20 - price) / ma20 * 100
                tags.append(StockTag(
                    tag="#低基期",
                    category="技術面",
                    score=75.0 + deviation,
                    evidence=f"股價({price:.2f})低於MA20({ma20:.2f}) {deviation:.1f}%"
                ))
            
            # #突破
            if volume > 0 and price > 0:
                avg_volume = tech_data.get("avg_volume", volume)
                if volume > avg_volume * 1.5:
                    tags.append(StockTag(
                        tag="#突破",
                        category="技術面",
                        score=70.0,
                        evidence=f"成交量({volume/1000000:.1f}M)為均量({avg_volume/1000000:.1f}M)的1.5倍"
                    ))
        
        # 3. 根據名稱添加主題標籤
        name_lower = name.lower()
        
        # #石化相關
        petro_keywords = ["台苯", "台化", "台塑", "石化", "SM", "苯乙烯"]
        if any(kw in name for kw in petro_keywords):
            tags.append(StockTag(
                tag="#石化",
                category="主題",
                score=90.0,
                evidence=f"名稱包含石化關鍵字"
            ))
            tags.append(StockTag(
                tag="#台塑集團",
                category="主題",
                score=85.0 if "台" in name else 60.0,
                evidence=f"名稱關聯台塑集團"
            ))
        
        # #AI概念
        ai_keywords = ["台積電", "輝達", "NVIDIA", "AI", "半導體", "晶片"]
        if any(kw in name for kw in ai_keywords):
            tags.append(StockTag(
                tag="#AI概念",
                category="主題",
                score=90.0,
                evidence=f"名稱關聯AI/半導體"
            ))
        
        # 4. 根據價格數據添加標籤
        if price_data:
            change = price_data.get("change", 0)
            if isinstance(change, str):
                try:
                    change = float(change.replace("%", "").replace("+", ""))
                except:
                    change = 0
            
            # #強勢
            if change > 5:
                tags.append(StockTag(
                    tag="#強勢",
                    category="技術面",
                    score=80.0 + change,
                    evidence=f"單日漲幅 {change:.1f}%"
                ))
            
            # #修正
            if change < -5:
                tags.append(StockTag(
                    tag="#修正",
                    category="技術面",
                    score=70.0 + abs(change),
                    evidence=f"單日跌幅 {change:.1f}%"
                ))
        
        # 5. 去重並排序
        unique_tags = {}
        for t in tags:
            if t.tag not in unique_tags:
                unique_tags[t.tag] = t
        
        return sorted(unique_tags.values(), key=lambda x: x.score, reverse=True)
    
    def filter_by_tags(self, stocks: List[Dict], tag_filters: List[str]) -> List[Dict]:
        """
        根據標籤篩選股票
        
        Args:
            stocks: 股票列表 [{'symbol': str, 'name': str, ...}]
            tag_filters: 標籤列表 ['#低PB', '#轉機']
        
        Returns:
            List[Dict]: 符合所有標籤條件的股票
        """
        filtered = []
        for stock in stocks:
            stock_tags = self.get_stock_tags(
                stock.get('symbol', ''),
                stock.get('name', ''),
                stock.get('market', '')
            )
            tag_names = [t.tag for t in stock_tags]
            
            if all(tag in tag_names for tag in tag_filters):
                filtered.append(stock)
        
        return filtered
    
    def get_tag_stats(self, stocks: List[Dict]) -> Dict[str, int]:
        """
        取得標籤統計
        
        Returns:
            Dict: {'標籤名稱': 數量}
        """
        stats = {}
        for stock in stocks:
            tags = self.get_stock_tags(
                stock.get('symbol', ''),
                stock.get('name', ''),
                stock.get('market', '')
            )
            for t in tags:
                stats[t.tag] = stats.get(t.tag, 0) + 1
        return stats
    
    def get_portfolio_summary(self, stocks: List[Dict]) -> str:
        """產生持股標籤摘要"""
        if not stocks:
            return "無持股數據"
        
        stats = self.get_tag_stats(stocks)
        summary = [f"📊 持股標籤統計 (共{len(stocks)}檔)"]
        summary.append("-" * 30)
        
        for tag, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
            pct = count / len(stocks) * 100
            bar = "█" * int(pct / 5)
            summary.append(f"  {tag}: {count}檔 ({pct:.0f}%) {bar}")
        
        return "\n".join(summary)


def get_stock_with_tags(symbol: str, name: str, market: str = "") -> Dict:
    """快速取得股票標籤"""
    tagger = StockTagger()
    tags = tagger.get_stock_tags(symbol, name, market)
    
    return {
        "symbol": symbol,
        "name": name,
        "market": market,
        "tags": [t.tag for t in tags],
        "tag_details": [(t.tag, t.evidence) for t in tags]
    }


if __name__ == "__main__":
    # 測試
    tagger = StockTagger()
    
    # 測試股票
    test_stocks = [
        ("1310.TW", "台苯", "台股"),
        ("2330.TW", "台積電", "台股"),
        ("1326.TW", "台化", "台股"),
        ("PLTR", "Palantir", "美股"),
    ]
    
    for symbol, name, market in test_stocks:
        result = get_stock_with_tags(symbol, name, market)
        print(f"\n📌 {name} ({symbol}) - {market}")
        print(f"   標籤: {', '.join(result['tags'])}")
        print(f"   佐證:")
        for tag, evidence in result['tag_details']:
            print(f"     • {tag}: {evidence}")
