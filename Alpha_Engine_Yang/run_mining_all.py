
import subprocess
import time
import os

stocks = ["PLTR", "TGT", "OXY", "1301.TW", "2317.TW", "2330.TW"]
log_file = "mining_progress.log"

def run_mining():
    with open(log_file, "a") as log:
        log.write(f"--- Mining Session Started at {time.ctime()} ---\n")
        
    for ticker in stocks:
        if os.path.exists(f"results/best_alpha_{ticker}.json"):
            print(f"Skipping {ticker}, already exists.")
            continue
            
        print(f"Starting mining for {ticker}...")
        start_time = time.time()
        
        try:
            # Run the engine for each stock as a module
            subprocess.run(["python3", "-m", "model_core.engine", ticker], check=True)
            
            elapsed = (time.time() - start_time) / 60
            with open(log_file, "a") as log:
                log.write(f"{ticker}: Success | Duration: {elapsed:.2f} min | Time: {time.ctime()}\n")
        except Exception as e:
            with open(log_file, "a") as log:
                log.write(f"{ticker}: Failed | Error: {str(e)} | Time: {time.ctime()}\n")
        
        # Optional: Sleep between runs to stay within the "2 hours per stock" limit or just finish early
        # print("Cooling down for 1 minute...")
        # time.sleep(60)

if __name__ == "__main__":
    run_mining()
