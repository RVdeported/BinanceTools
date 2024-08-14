from binance.um_futures import UMFutures
from binance.cm_futures import CMFutures
import time
from termcolor import colored
import sys

def read_keys():
    with open("keys.txt", "r") as f:
        public = f.readline()[:-1]
        secret = f.readline()[:-1]
    return public, secret

public, secret = read_keys()

clientUM = UMFutures(key=public, secret=secret)
clientCM = CMFutures(key=public, secret=secret)

def get_positions(UM):
    client = clientUM if UM else clientCM
    res = client.account()
    assets = res["positions"]
    assets_with_pos = [ass for ass in assets if abs(float(ass["positionAmt"])) > 1e-10]
    return assets_with_pos, res

def get_positions_str(UM = True, col = False):
    assets, acc_info = get_positions(UM)
    out = ""
    if UM:
        out +="Available Balance: {}\tUPNL:{}\tWithMargin: {}\n".format(
                acc_info["availableBalance"], acc_info["totalCrossUnPnl"], 
                float(acc_info["availableBalance"]) + 
                float(acc_info["totalInitialMargin"]))
    for n in assets:
        s = "{}:\tentryPx:{}\tAmnt:{}\tUPNL:{:.2f}({:.2f}%)\tNotional:{}\n"\
                .format(n["symbol"], n["entryPrice"],n["positionAmt"], 
                        float(n["unrealizedProfit"]), 
                        float(n["unrealizedProfit"]) \
                            / (abs(float(n["notional"])) * 100.0
                               if UM else
                               float(n["initialMargin"])
                        ),
                        n["notional"] if UM else 0)        
        color = "green" if float(n["positionAmt"]) > 0 else "yellow"
        out += colored(s, color ) if col else s

    return out


def display_help():
    print("Displays curr positions\nPARAMS: [{um|cm} [UpdFreqSec")

if __name__ == "__main__":
    if "--help" in sys.argv:
        display_help()
        exit(0)
    if (len(sys.argv) > 1 and sys.argv[1] not in ["um", "cm"]):
        display_help()
        exit(1)

    UM = sys.argv[1] == "um" if len(sys.argv) > 1 else True
    freq_upd_sec = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    while(True):
        print(get_positions_str(UM, True))        
        time.sleep(freq_upd_sec)

