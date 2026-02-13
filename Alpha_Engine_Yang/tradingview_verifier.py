
import json
import os

class TradingViewExporter:
    """
    Converts AlphaGPT formulas (Reverse Polish Notation / Stack-based) to Pine Script.
    """
    def __init__(self):
        self.features_map = {
            'RET': 'close / close[1] - 1',
            'VOL': 'volume',
            'V_CHG': 'volume / volume[1] - 1',
            'PV': '(close / close[1] - 1) * volume',
            'TREND': 'ta.sma(close, 20) / ta.sma(close, 60) - 1'
        }
        
        self.ops_map = {
            'ADD': ('({} + {})', 2),
            'SUB': ('({} - {})', 2),
            'MUL': ('({} * {})', 2),
            'DIV': ('({} / ({} + 1e-6))', 2),
            'NEG': ('(-{})', 1),
            'ABS': ('math.abs({})', 1),
            'SIGN': ('math.sign({})', 1),
            'GATE': ('({} > 0 ? {} : {})', 3),
            'JUMP': ('(ta.stdev({}, 20) > 0 ? ({} - ta.sma({}, 20)) / ta.stdev({}, 20) : 0)', 1), # Simplified
            'DECAY': ('({} + 0.8 * {}[1] + 0.6 * {}[2])', 1),
            'DELAY1': ('{}[1]', 1),
            'MAX3': ('math.max({}, math.max({}[1], {}[2]))', 1)
        }
        
        self.vocab = ['RET', 'VOL', 'V_CHG', 'PV', 'TREND'] + \
                     ['ADD', 'SUB', 'MUL', 'DIV', 'NEG', 'ABS', 'SIGN', 'GATE', 'JUMP', 'DECAY', 'DELAY1', 'MAX3']

    def to_pine(self, formula_tokens, strategy_name="Alpha_Engine_Yang_Strategy"):
        stack = []
        
        for token_idx in formula_tokens:
            if token_idx >= len(self.vocab):
                continue
                
            token = self.vocab[token_idx]
            
            if token in self.features_map:
                stack.append(self.features_map[token])
            elif token in self.ops_map:
                template, num_args = self.ops_map[token]
                if len(stack) < num_args:
                    # Not enough arguments, push a placeholder or skip
                    continue
                
                args = [stack.pop() for _ in range(num_args)]
                # Reverse args because they were popped from stack
                args = args[::-1]
                
                if token == 'JUMP':
                    # JUMP template has 4 slots for the same arg
                    val = args[0]
                    expr = template.format(val, val, val, val)
                elif token == 'DECAY' or token == 'MAX3':
                    val = args[0]
                    expr = template.format(val, val, val)
                else:
                    expr = template.format(*args)
                    
                stack.append(expr)
        
        if not stack:
            return "// Error: Empty stack or invalid formula"
            
        final_alpha = stack[-1]
        
        pine_script = f"""// @version=5
strategy("{strategy_name}", overlay=false)

// Features and Ops implementation
alpha_val = {final_alpha}

// Signals
long_condition = ta.crossover(alpha_val, ta.sma(alpha_val, 20))
short_condition = ta.crossunder(alpha_val, ta.sma(alpha_val, 20))

if (long_condition)
    strategy.entry("Long", strategy.long)

if (short_condition)
    strategy.close("Long")

plot(alpha_val, title="Alpha Value", color=color.blue)
hline(0, "Zero Line", color=color.gray)
"""
        return pine_script

def export_best_strategy(input_file="best_meme_strategy.json", output_file="strategy.pine"):
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return
        
    with open(input_file, "r") as f:
        formula = json.load(f)
        
    exporter = TradingViewExporter()
    pine = exporter.to_pine(formula)
    
    with open(output_file, "w") as f:
        f.write(pine)
    
    print(f"✓ Pine Script exported to {output_file}")

if __name__ == "__main__":
    export_best_strategy()
