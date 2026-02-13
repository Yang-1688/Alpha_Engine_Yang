
import pandas as pd
import torch
import os
from .factors import FeatureEngineer

class StockDataLoader:
    def __init__(self, data_dir="data", device="cpu"):
        self.data_dir = data_dir
        self.device = device
        self.feat_tensor = None
        self.raw_data_cache = None
        self.target_ret = None
        self.tickers = []

    def load_stock_data(self, ticker):
        """Load specific stock data from CSV and prepare tensors."""
        self.tickers = [ticker]
        filename = f"{self.data_dir}/{ticker.replace('.', '_')}_5y.csv"
        
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Data file not found: {filename}")
            
        print(f"Loading {ticker} data from {filename}...")
        
        # Load CSV - yfinance format usually has multi-index headers
        # We need to skip rows or use header=[0,1]
        df = pd.read_csv(filename, header=[0,1], index_col=0, parse_dates=True)
        
        # Prepare Tensors [Ticker, Time] - here Ticker is 1
        def to_tensor(col_name):
            # Ticker is usually in the second level
            vals = df[col_name][ticker].ffill().fillna(0.0).values
            return torch.tensor(vals.reshape(1, -1), dtype=torch.float32, device=self.device)

        self.raw_data_cache = {
            'open': to_tensor('Open'),
            'high': to_tensor('High'),
            'low': to_tensor('Low'),
            'close': to_tensor('Close'),
            'volume': to_tensor('Volume'),
            # Stock data typically doesn't have liquidity/fdv in yfinance
            'liquidity': torch.ones_like(to_tensor('Close')) * 1e9,
            'fdv': torch.ones_like(to_tensor('Close')) * 1e9
        }
        
        # Compute features using the shared AlphaGPT FeatureEngineer
        self.feat_tensor = FeatureEngineer.compute_features(self.raw_data_cache)
        
        # Target returns (next-period log returns)
        # Using Open to Open for backtest consistency or Close to Close
        cl = self.raw_data_cache['close']
        self.target_ret = torch.log(torch.roll(cl, -1, dims=1) / (cl + 1e-9))
        self.target_ret[:, -1] = 0.0 # Last one has no future
        
        print(f"Data Ready for {ticker}. Shape: {self.feat_tensor.shape}")
