from pybit.unified_trading import HTTP
from pprint import pprint
import time
import sys
import re
import os
from math import ceil
import configparser
from tabulate import tabulate
import datetime as dt
import time




def help():
    print("USAGE: [api_key_set [command+args\norders\ncancel\ntrade [symbol [qty" + 
            "\nclose\npositions\nlimit [symbol [qty [px\nposslim\ntrades\n")

def get_px(cli: HTTP, ass):
    res = cli.get_tickers(category = "linear", symbol = ass)
    return float(res["result"]["list"][0]["ask1Price"])

def acc_info(cli: HTTP):
    res = cli.get_positions(category="linear", settleCoin="USDT")
    positions = res["result"]["list"]
    out = [["Instr", "Qt", "Amn", "tupnl"]]

    total_pnl       = 0.0
    total_assets    = 0.0
    total_exposure  = 0.0
    total_margin    = 0.0
    for pos in positions:
        ass    = pos["symbol"]
        isLong = pos["side"] == "Buy"
        qt = float(pos["size"]) * (1.0 if isLong else -1.0)
        amt= float(pos["positionValue"]) * (1.0 if isLong else -1.0)
        pnl= float(pos["unrealisedPnl"])

        out += [[ass, qt, amt, pnl]]
        total_pnl += pnl
        total_exposure += abs(amt)
    

    res = cli.get_wallet_balance(accountType="UNIFIED")
    pprint(res)
    print(tabulate(out))
    print("\nASSETS:\n")
    out = []
    assets = res["result"]["list"][0]["coin"]
    for ass in assets:
        asset = ass["coin"]
        qt    = float(ass["walletBalance"])
        amt   = float(ass["usdValue"]) 
        out  += [[asset, qt, amt]]
        total_assets += amt
        total_margin += float(ass["totalPositionIM"])

    print(tabulate(out))
    print(f"TOTAL EXPOSURE\t{total_exposure}")
    print(f"TOTAL UPNL\t{total_pnl}")
    print(f"TOTAL AVL ASSETS\t{total_assets}")


def trade(cli: HTTP, ass, qt, reduce=True):
    res = cli.place_order(
        category="linear", 
        symbol  =ass,
        side    ="Buy" if qt > 0.0 else "Sell",
        orderType="Market",
        qty     =abs(qt),
        reduceOnly=reduce)
    return res

def limit(cli, ass, qt, px):
    res = cli.place_order(
        category="linear",
        symbol  =ass,
        side    ="Buy" if qt > 0.0 else "Sell",
        orderType="Limit",
        qty     =abs(qt),
        price   =px
    )

    return res

def trades(cli):
    res = cli.get_executions(category="linear", limit=50)
    rows = []
    for tr in res["result"]["list"]:
        itm = [
          dt.datetime.fromtimestamp(int(tr["execTime"]) // 1000), 
          tr["orderLinkId"],
          tr["side"],
          tr["execPrice"],
          tr["execQty"],
          tr["orderQty"]
        ]
        rows.append(itm)

    rows = sorted(rows, key=lambda x: x[0], reverse=True)
    tab = tabulate(rows, headers=["ts", "id", "side", "px", "execQt", "origQt"])
    return tab

def close(cli):
    poss = cli.get_positions(category="linear", settleCoin="USDT")
    for pos in poss["result"]["list"]:
        ass = pos["symbol"]
        isLong = pos["side"] == "Buy"
        qt = float(pos["size"]) * (1.0 if isLong else -1.0)
        amt= float(pos["positionValue"]) * (1.0 if isLong else -1.0)
        if abs(qt) <= 0.0:
            continue
        if (abs(amt) <= 5):
            continue
        
        print(trade(cli, ass, -qt, True))

def orders(cli):
    orders = cli.get_open_orders(
        category="linear", 
        settleCoin="USDT",
        openOnly  =0
    )
    ords = []
    for ord in orders["result"]["list"]:
        isLong = ord["side"] == "Buy"
        itms = [
            ord["symbol"],
            float(ord["leavesQty"]) * 1.0 if isLong else -1.0,
            ord["price"],
            ord["orderLinkId"]
        ]
        
        ords.append(itms)
        
    tab = tabulate(ords, headers=["Symbol", "qt", "px", "id"])
    return tab

def cancel(cli):
    res = cli.cancel_all_orders(
        category="linear",
        settleCoin="USDT"
    )
    return res 

if __name__ == "__main__":
    args = sys.argv

    id  = args[1] 
    keys = configparser.ConfigParser()
    keys.read("FutKeys.ini")
    api = keys[f"ACC_{id}"]["api_key"]
    sec = keys[f"ACC_{id}"]["secret"]
    cli = HTTP(testnet=False, api_key=api, api_secret=sec)

    args[2] = args[2].lower()
    if     (args[2] == "posslim"):
        acc_info(cli)
    elif (args[2] == "trade"):
        if (len(args) < 5):
            help()
            exit(0)
        pprint(trade(cli, args[3], float(args[4]), False))
    elif (args[2] == "limit"):
        if (len(args) < 6):
            help()
            exit(0)
        pprint(limit(cli, args[3], float(args[4]), float(args[5])))
    elif (args[2] == "close"):
        close(cli)
        acc_info(cli)
    elif (args[2] == "cancel"):
        cancel(cli)
    elif (args[2] == "orders"):
        orders(cli)
    elif (args[2] == "reset"):
        cancel(cli)
        close(cli)
        acc_info(cli)
    elif (args[2] == "trades"):
        print(trades(cli))
    else:
        help()
 
