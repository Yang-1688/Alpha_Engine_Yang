#!/usr/bin/env python3
"""
台股籌碼分析器 | Taiwan Stock Chip Analyzer
來源: wantgoo.com 股權分散
功能: 分析大戶/散戶籌碼變化，產生籌碼標籤

籌碼標籤邏輯:
- #籌碼健康: 大戶持股上升 + 散戶持股下降
- #籌碼凌亂: 大戶持股下降 + 散戶持股上升
- #籌碼中性: 變化不大
- #籌碼集中: 大戶持股上升(不論散戶)
- #籌碼分散: 散戶持股上升(不論大戶)

使用方法:
    from skills.stock_tagger.chip_analyzer import ChipAnalyzer
    chip = ChipAnalyzer()
    result = chip.analyze_chip("2330.TW", "台積電")
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime, timedelta


# ============ 模擬籌碼數據 (實際應从 API/網站抓取) ============
# 這些數據應該從 wantgoo.com 或其他來源取得
# 格式: {代號: {'大戶持股%(20天前)': float, '大戶持股%(最新)': float, '散戶持股%(20天前)': float, '散戶持股%(最新)': float}}

CHIP_DATA_SAMPLE = {
    "2330.TW": {
        "name": "台積電",
        "institutional_20d_ago": 89.23,  # 大戶20天前
        "institutional_now": 89.10,      # 大戶最新
        "retail_20d_ago": 5.11,          # 散戶20天前
        "retail_now": 5.17,              # 散戶最新
    },
    "1310.TW": {
        "name": "台苯",
        "institutional_20d_ago": 78.5,
        "institutional_now": 79.2,
        "retail_20d_ago": 12.3,
        "retail_now": 11.8,
    },
    "1326.TW": {
        "name": "台化",
        "institutional_20d_ago": 82.1,
        "institutional_now": 81.5,
        "retail_20d_ago": 8.9,
        "retail_now": 9.2,
    },
    "2317.TW": {
        "name": "鴻海",
        "institutional_20d_ago": 85.2,
        "institutional_now": 86.1,
        "retail_20d_ago": 7.5,
        "retail_now": 7.2,
    },
}


@dataclass
class ChipAnalysis:
    """籌碼分析結果"""
    symbol: str
    name: str
    
    # 籌碼數據
    institutional_pct_20d: float  # 大戶20天前
    institutional_pct_now: float  # 大戶最新
    retail_pct_20d: float         # 散戶20天前
    retail_pct_now: float         # 散戶最新
    
    # 變化
    institutional_change: float   # 大戶變化
    retail_change: float          # 散戶變化
    
    # 標籤
    chip_tag: str                 # 籌碼標籤
    chip_score: int               # 籌碼分數 (0-100)
    analysis: str                 # 分析說明


class ChipAnalyzer:
    """台股籌碼分析器"""
    
    def __init__(self):
        self.data = CHIP_DATA_SAMPLE
    
    def fetch_chip_data(self, symbol: str, name: str = "") -> Dict:
        """
        抓取籌碼數據
        
        Args:
            symbol: 股票代號 (如 2330.TW)
            name: 股票名稱
        
        Returns:
            Dict: 籌碼數據
        """
        # 優先使用預設數據
        if symbol in self.data:
            return self.data[symbol]
        
        # 嘗試從 API 抓取 (預留)
        # url = f"https://www.wantgoo.com/stock/{symbol.replace('.TW', '')}/shareholding-distribution"
        
        return None
    
    def analyze_chip(self, symbol: str, name: str = "") -> Optional[ChipAnalysis]:
        """
        分析籌碼結構
        
        Args:
            symbol: 股票代號
            name: 股票名稱
        
        Returns:
            ChipAnalysis: 籌碼分析結果 或 None
        """
        data = self.fetch_chip_data(symbol, name)
        
        if data is None:
            return None
        
        # 計算變化
        inst_change = data["institutional_now"] - data["institutional_20d_ago"]
        retail_change = data["retail_now"] - data["retail_20d_ago"]
        
        # 判斷籌碼標籤
        if inst_change > 0.5 and retail_change < -0.3:
            # 大戶上升，散戶下降 → 健康
            chip_tag = "#籌碼健康"
            chip_score = 80 + min(inst_change * 5, 20)
            analysis = f"籌碼往大戶集中！大戶持股增加 {inst_change:.2f}%，散戶減少 {abs(retail_change):.2f}%，安全信號。"
        
        elif inst_change < -0.5 and retail_change > 0.3:
            # 大戶下降，散戶上升 → 凌亂
            chip_tag = "#籌碼凌亂"
            chip_score = 30 - min(abs(inst_change) * 5, 25)
            analysis = f"籌碼往散戶集中！大戶持股減少 {abs(inst_change):.2f}%，散戶增加 {retail_change:.2f}%，危險信號。"
        
        elif inst_change > 0.5:
            # 大戶上升，散戶變化不大 → 集中
            chip_tag = "#籌碼集中"
            chip_score = 65 + min(inst_change * 3, 15)
            analysis = f"大戶持股增加 {inst_change:.2f}%，籌碼開始集中。"
        
        elif retail_change > 0.5:
            # 散戶上升，大戶變化不大 → 分散
            chip_tag = "#籌碼分散"
            chip_score = 45 - min(retail_change * 3, 15)
            analysis = f"散戶持股增加 {retail_change:.2f}%，籌碼開始分散。"
        
        else:
            # 變化不大 → 中性
            chip_tag = "#籌碼中性"
            chip_score = 50
            analysis = f"籌碼變化不大，大戶 {inst_change:+.2f}%，散戶 {retail_change:+.2f}%。"
        
        return ChipAnalysis(
            symbol=symbol,
            name=data.get("name", name),
            institutional_pct_20d=data["institutional_20d_ago"],
            institutional_pct_now=data["institutional_now"],
            retail_pct_20d=data["retail_20d_ago"],
            retail_pct_now=data["retail_now"],
            institutional_change=inst_change,
            retail_change=retail_change,
            chip_tag=chip_tag,
            chip_score=chip_score,
            analysis=analysis
        )
    
    def get_chip_report(self, symbol: str, name: str = "") -> str:
        """產生籌碼分析報告"""
        result = self.analyze_chip(symbol, name)
        
        if result is None:
            return f"⚠️ 無法取得 {name} ({symbol}) 的籌碼數據"
        
        report = []
        report.append("=" * 60)
        report.append(f"📊 籌碼分析 | {result.name} ({result.symbol})")
        report.append("=" * 60)
        report.append(f"📅 分析時間: {datetime.now().strftime('%Y-%m-%d')}")
        report.append("")
        
        # 籌碼數據
        report.append("📈 **籌碼數據**")
        report.append(f"  ┌────────────────────┬────────────┬────────────┬──────────┐")
        report.append(f"  │                    │   20天前   │   最新     │   變化   │")
        report.append(f"  ├────────────────────┼────────────┼────────────┼──────────┤")
        report.append(f"  │ 大戶持股比例        │   {result.institutional_pct_20d:5.2f}%   │   {result.institutional_pct_now:5.2f}%   │  {result.institutional_change:+5.2f}%  │")
        report.append(f"  │ 散戶持股比例        │   {result.retail_pct_20d:5.2f}%   │   {result.retail_pct_now:5.2f}%   │  {result.retail_change:+5.2f}%  │")
        report.append(f"  └────────────────────┴────────────┴────────────┴──────────┘")
        report.append("")
        
        # 籌碼標籤
        report.append(f"🏷️ **籌碼標籤**: {result.chip_tag}")
        report.append(f"   **籌碼分數**: {result.chip_score}/100")
        report.append("")
        
        # 分析說明
        report.append(f"💡 **分析**: {result.analysis}")
        report.append("")
        
        # 風險提示
        if result.chip_tag == "#籌碼凌亂":
            report.append("⚠️ **風險提示**: 籌碼開始往散戶集中，建議謹慎操作或考慮減碼。")
        elif result.chip_tag == "#籌碼健康":
            report.append("✅ **機會提示**: 籌碼往大戶集中，可逢低布局。")
        
        report.append("")
        report.append("=" * 60)
        report.append("🔗 資料來源: wantgoo.com 股權分散")
        
        return "\n".join(report)


def get_chip_tag_for_stock(symbol: str, name: str = "") -> Dict:
    """
    快速取得股票籌碼標籤 (供標籤系統使用)
    
    Returns:
        Dict: {'tag': str, 'score': int, 'evidence': str}
    """
    analyzer = ChipAnalyzer()
    result = analyzer.analyze_chip(symbol, name)
    
    if result is None:
        return {"tag": "#無籌碼數據", "score": 50, "evidence": "無法取得籌碼資料"}
    
    return {
        "tag": result.chip_tag,
        "score": result.chip_score,
        "evidence": result.analysis
    }


if __name__ == "__main__":
    # 測試
    analyzer = ChipAnalyzer()
    
    test_stocks = [
        ("2330.TW", "台積電"),
        ("1310.TW", "台苯"),
        ("1326.TW", "台化"),
        ("2317.TW", "鴻海"),
    ]
    
    for symbol, name in test_stocks:
        print("\n" + "=" * 60)
        print(analyzer.get_chip_report(symbol, name))
