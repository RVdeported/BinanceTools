from binance.um_futures import UMFutures
import time
from termcolor import colored
import sys

def read_keys():
    with open("keys.txt", "r") as f:
        public = f.readline()[:-1]
        secret = f.readline()[:-1]
    return public, secret

public, secret = read_keys()

client = UMFutures(key=public, secret=secret)

def get_positions():
    res = client.account()
    assets = res["positions"]
    assets_with_pos = [ass for ass in assets if abs(float(ass["positionAmt"])) > 1e-10]
    return assets_with_pos, res

if __name__ == "__main__":
    freq_upd_sec = int(sys.argv[1]) if len(sys.argv) == 2 else 10
    while(True):
        assets, acc_info = get_positions()
        print("Available Balance: {}\tUPNL:{}\tWithMargin: {}".format(
            acc_info["availableBalance"], acc_info["totalCrossUnPnl"], 
            float(acc_info["availableBalance"]) + float(acc_info["totalInitialMargin"])))
        for n in assets:
            print(colored(
                "{}:\tentryPx:{}\tAmnt:{}\tUPNL:{:.2f}({:.2f}%)\tNotional:{}"\
                .format(n["symbol"], n["entryPrice"],n["positionAmt"], float(n["unrealizedProfit"]), 
                        float(n["unrealizedProfit"]) / abs(float(n["notional"])) * 100.0,
                        n["notional"]), 
                "green" if float(n["positionAmt"]) > 0 else "yellow"))

        time.sleep(freq_upd_sec)

