import yfinance as yf
import json

def get_market_news():
    tickers = {
        "US": "^GSPC",
        "China": "000001.SS",
        "Hong Kong": "^HSI",
        "Taiwan": "^TWII"
    }
    
    all_news = []
    for market, symbol in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            if news:
                # Add market info to news items
                for item in news[:2]: # Get top 2 from each
                    item['market'] = market
                    all_news.append(item)
        except Exception as e:
            print(f"Error fetching news for {market}: {e}")
            
    return all_news

if __name__ == "__main__":
    news_data = get_market_news()
    print(json.dumps(news_data, indent=2))
