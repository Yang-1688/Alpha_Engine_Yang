import yfinance as yf
import pandas as pd
import sys

def fetch_data(symbol, period="1mo"):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        if df.empty:
            print(f"No data found for {symbol}")
            return None
        
        filename = f"{symbol}_history.csv"
        df.to_csv(filename)
        print(f"Successfully saved data for {symbol} to {filename}")
        return filename
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    fetch_data(symbol)
