
import torch
from torch.distributions import Categorical
from tqdm import tqdm
import json
import os

from .config import ModelConfig
from .data_loader import StockDataLoader
from .alphagpt import AlphaGPT, NewtonSchulzLowRankDecay, StableRankMonitor
from .vm import StackVM
from .backtest import MemeBacktest

class AlphaEngine:
    def __init__(self, ticker, use_lord_regularization=True, lord_decay_rate=1e-3, lord_num_iterations=5):
        self.ticker = ticker
        self.loader = StockDataLoader(device=str(ModelConfig.DEVICE))
        self.loader.load_stock_data(ticker)
        
        self.model = AlphaGPT().to(ModelConfig.DEVICE)
        self.opt = torch.optim.AdamW(self.model.parameters(), lr=1e-3)
        
        self.use_lord = use_lord_regularization
        if self.use_lord:
            self.lord_opt = NewtonSchulzLowRankDecay(
                self.model.named_parameters(),
                decay_rate=lord_decay_rate,
                num_iterations=lord_num_iterations,
                target_keywords=["q_proj", "k_proj", "attention", "qk_norm"]
            )
            self.rank_monitor = StableRankMonitor(self.model)
        
        self.vm = StackVM()
        self.bt = MemeBacktest()
        
        self.best_score = -float('inf')
        self.best_formula = None

    def train(self, steps=1000):
        print(f"🚀 Training Alpha for {self.ticker}...")
        pbar = tqdm(range(steps))
        
        for step in pbar:
            bs = 1024 # Reduced batch size for stability and resource efficiency
            inp = torch.zeros((bs, 1), dtype=torch.long, device=ModelConfig.DEVICE)
            
            log_probs = []
            tokens_list = []
            
            for _ in range(ModelConfig.MAX_FORMULA_LEN):
                logits, _, _ = self.model(inp)
                dist = Categorical(logits=logits)
                action = dist.sample()
                
                log_probs.append(dist.log_prob(action))
                tokens_list.append(action)
                inp = torch.cat([inp, action.unsqueeze(1)], dim=1)
            
            seqs = torch.stack(tokens_list, dim=1)
            rewards = torch.zeros(bs, device=ModelConfig.DEVICE)
            
            # Vectorized VM execution if possible, but StackVM is usually sequential per formula
            # Using loop for now but limited BS
            for i in range(bs):
                formula = seqs[i].tolist()
                res = self.vm.execute(formula, self.loader.feat_tensor)
                
                if res is None or res.std() < 1e-4:
                    rewards[i] = -5.0
                    continue
                
                score, ret_val = self.bt.evaluate(res, self.loader.raw_data_cache, self.loader.target_ret)
                rewards[i] = score
                
                if score.item() > self.best_score:
                    self.best_score = score.item()
                    self.best_formula = formula
            
            adv = (rewards - rewards.mean()) / (rewards.std() + 1e-5)
            loss = 0
            for t in range(len(log_probs)):
                loss += -log_probs[t] * adv
            
            loss = loss.mean()
            self.opt.zero_grad()
            loss.backward()
            self.opt.step()
            
            if self.use_lord:
                self.lord_opt.step()
            
            pbar.set_postfix({'Score': f"{self.best_score:.3f}"})

        # Save result
        os.makedirs("results", exist_ok=True)
        with open(f"results/best_alpha_{self.ticker}.json", "w") as f:
            json.dump({"ticker": self.ticker, "score": self.best_score, "formula": self.best_formula}, f)
        
        print(f"✓ {self.ticker} Completed. Best Score: {self.best_score:.4f}")

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "PLTR"
    eng = AlphaEngine(ticker)
    eng.train(steps=ModelConfig.TRAIN_STEPS)
