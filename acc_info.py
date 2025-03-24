from binance.um_futures import UMFutures
from binance.cm_futures import CMFutures
import time
from termcolor import colored
import sys
import configparser as cp

INSTR_PRICE = {
        "BTC" : 90000,
        "ETH" : 3300,
        "DOGE": 0.1,
        "MATIC":0.45,
        "SOL" : 140,
        "XRP" : 0.5,
        "LTC" : 60,
        "LINK": 10,
        "FIL" : 3.5,
        "ADA" : 0.33,
        "AVA" : 20.6,
        "BNB" : 520,
        "USDT":1,
        "USD" :1
    }


def read_keys(id):
    conf = cp.ConfigParser()
    conf.read("FutKeys.ini") 
    
    public = conf[f"ACC_{id}"]["api_key"]
    secret = conf[f"ACC_{id}"]["secret"]
    return public, secret

public, secret = read_keys(1)

clientUM = UMFutures(key=public, secret=secret)
clientCM = CMFutures(key=public, secret=secret)

def set_client(id):
    global clientUM, clientCM
    public, secret = read_keys(id)

    clientUM = UMFutures(key=public, secret=secret)
    clientCM = CMFutures(key=public, secret=secret)
    return clientUM, clientCM


def get_positions(UM):
    client = clientUM if UM else clientCM
    res = client.account()
    assets = res["positions"]
    assets_with_pos = [ass for ass in assets if abs(float(ass["positionAmt"])) > 1e-10]
    return assets_with_pos, res

def get_positions_str(UM = True, col = False):
    assets, acc_info = get_positions(UM)
    cli = clientUM if UM else clientCM
    out = ""
    if UM:
        out +="Available Balance: {}\tUPNL:{}\tWithMargin: {}\n".format(
                acc_info["availableBalance"], acc_info["totalCrossUnPnl"], 
                float(acc_info["availableBalance"]) + 
                float(acc_info["totalInitialMargin"]))
    for n in assets:
        px          = float(cli.book_ticker(n["symbol"])["askPrice"])
        upnl        = float(n["unrealizedProfit"]) 
        notional    = float(n["positionAmt"]) * (px if UM else
                            (100 if n["symbol"] == "BTCUSD_PERP" else 10))
        upnl_perc   = upnl / abs(notional) * 100
        s = "{}:\tAmnt:{}\tUPNL:{:.2f}({:.2f}%)\tNotional:{}\n"\
                .format(n["symbol"],n["positionAmt"], 
                        upnl, upnl_perc, notional 
                        )        
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
