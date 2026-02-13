import yfinance as yf
import json

def get_china_hk_news():
    tickers = [
        "9988.HK", "9626.HK", "1024.HK", "0338.HK", "3968.HK", 
        "0017.HK", "2601.HK", "002230.SZ", "600028.SS", "002352.SZ"
    ]
    
    results = []
    for symbol in tickers:
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            if news:
                for item in news[:2]:
                    item['symbol'] = symbol
                    results.append(item)
                    if len(results) >= 15: break
        except:
            continue
        if len(results) >= 15: break
            
    return results[:10]

if __name__ == "__main__":
    news_data = get_china_hk_news()
    print(json.dumps(news_data, indent=2))
