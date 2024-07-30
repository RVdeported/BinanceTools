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

def get_positions_str(col = False):
    assets, acc_info = get_positions()
    out ="Available Balance: {}\tUPNL:{}\tWithMargin: {}\n".format(
            acc_info["availableBalance"], acc_info["totalCrossUnPnl"], 
            float(acc_info["availableBalance"]) + 
            float(acc_info["totalInitialMargin"]))
    for n in assets:
        s = "{}:\tentryPx:{}\tAmnt:{}\tUPNL:{:.2f}({:.2f}%)\tNotional:{}\n"\
                .format(n["symbol"], n["entryPrice"],n["positionAmt"], 
                        float(n["unrealizedProfit"]), 
                        float(n["unrealizedProfit"]) \
                            / abs(float(n["notional"])) * 100.0,
                        n["notional"])        
        color = "green" if float(n["positionAmt"]) > 0 else "yellow"
        out += colored(s, color ) if col else s

    return out



if __name__ == "__main__":
    freq_upd_sec = int(sys.argv[1]) if len(sys.argv) == 2 else 10
    while(True):
        print(get_positions_str(True))        
        time.sleep(freq_upd_sec)

