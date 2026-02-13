
import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

def fetch_stock_data(tickers, years=5):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years*365)
    
    os.makedirs("data", exist_ok=True)
    
    for ticker in tickers:
        print(f"Fetching {ticker}...")
        try:
            data = yf.download(ticker, start=start_date, end=end_date)
            if not data.empty:
                filename = f"data/{ticker.replace('.', '_')}_5y.csv"
                data.to_csv(filename)
                print(f"Saved to {filename}")
            else:
                print(f"No data for {ticker}")
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")

if __name__ == "__main__":
    stocks = ["PLTR", "TGT", "OXY", "1301.TW", "2317.TW", "2330.TW"]
    fetch_stock_data(stocks)
