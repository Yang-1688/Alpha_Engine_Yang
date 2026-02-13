
import os
import json
from datetime import datetime

def report_progress():
    workspace_path = "/home/node/.openclaw/workspace/Alpha_Engine_Yang"
    log_path = os.path.join(workspace_path, "mining_progress.log")
    results_path = os.path.join(workspace_path, "results")
    
    tickers = ["PLTR", "TGT", "OXY", "1301.TW", "2317.TW", "2330.TW"]
    completed = []
    failed = []
    in_progress = None
    
    if os.path.exists(results_path):
        for f in os.listdir(results_path):
            if f.startswith("best_alpha_") and f.endswith(".json"):
                ticker = f.replace("best_alpha_", "").replace(".json", "")
                completed.append(ticker)
    
    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            lines = f.readlines()
            for line in reversed(lines):
                if "Failed" in line:
                    t = line.split(":")[0].strip()
                    if t not in failed and t not in completed:
                        failed.append(t)
                if "Starting mining for" in line:
                    t = line.replace("Starting mining for", "").strip().replace("...", "")
                    if t not in completed and t not in failed:
                        in_progress = t
                        break

    report = f"📊 **Alpha 挖掘進度回報** ({datetime.now().strftime('%m/%d %H:%M')})\n\n"
    report += f"✅ **已完成**: {', '.join(completed) if completed else '無'}\n"
    report += f"⏳ **進行中**: {in_progress if in_progress else '無'}\n"
    report += f"❌ **失敗**: {', '.join(failed) if failed else '無'}\n"
    report += f"📈 **待處理**: {', '.join([t for t in tickers if t not in completed and t != in_progress])}\n"
    
    return report

if __name__ == "__main__":
    print(report_progress())
