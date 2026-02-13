# Alpha_Engine_Yang

🚀 An enhanced Quantitative Backtesting Engine based on AlphaGPT.

## Features

- **AlphaGPT Core**: Generates alpha factors using LLM-driven sequences.
- **Backtesting Engine**: Optimized for fast evaluation of mined strategies.
- **TradingView Integration**: Export mined strategies directly to TradingView Pine Script for verification.
- **LoRD Regularization**: Low-Rank Decay for stable and generalizable feature learning.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### 1. Mine Alphas
Run the core engine to find the best performing alpha formulas.

```bash
python model_core/engine.py
```

### 2. Export to TradingView
After mining, convert the best formula into Pine Script for validation on TradingView charts.

```bash
python tradingview_verifier.py
```

## Structure

- `model_core/`: Core AlphaGPT logic and virtual machine for formula execution.
- `data_pipeline/`: Data fetching and processing.
- `strategy_manager/`: Portfolio management and risk control.
- `dashboard/`: Visualization tools.

---
*Created and maintained by Yang-1688*
