import yfinance as yf
import json
import sys

def get_portfolio_news():
    # Mapping logic
    a_shares = [
        "601611.SS", "688262.SS", "300520.SZ", "688012.SS", "601118.SS", 
        "002230.SZ", "603389.SS", "600028.SS", "688699.SS", "300157.SZ", 
        "002352.SZ", "600256.SS", "601601.SS", "601336.SS", "601658.SS", 
        "601728.SS", "601668.SS", "603393.SS", "002648.SZ", "002493.SZ", "002714.SZ"
    ]
    hk_shares = [
        "1880.HK", "9988.HK", "9880.HK", "9626.HK", "6936.HK", "0017.HK", 
        "3968.HK", "1024.HK", "9699.HK", "0338.HK", "7568.HK", "0669.HK", "2601.HK"
    ]
    us_shares = [
        "AMSC", "PFE", "NVO", "RIG", "OKE", "MRNA", "MOS", "COP", "OXY", "CVX", "PLTR"
    ]
    
    all_tickers = a_shares + hk_shares + us_shares
    
    # Prioritize some big names to ensure we get news if searching all takes too long
    # But here we'll just try to get a few from each group
    results = []
    
    # Sample some from each to stay within time/limit
    to_check = us_shares + hk_shares[:5] + a_shares[:5]
    
    for symbol in to_check:
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            if news:
                for item in news[:1]:
                    item['symbol'] = symbol
                    results.append(item)
                    if len(results) >= 15: break
        except:
            continue
        if len(results) >= 15: break
            
    return results[:10]

if __name__ == "__main__":
    news_data = get_portfolio_news()
    print(json.dumps(news_data, indent=2))
