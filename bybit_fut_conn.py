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

def acc_info(clis: list[HTTP]):
    poss = {}
    ress= []
    total_pnl       = 0.0
    total_assets    = 0.0
    total_exposure  = 0.0
    total_margin    = 0.0
    for cli in clis:
        res = cli.get_positions(category="linear", settleCoin="USDT")
        ress.append(res)
        positions = res["result"]["list"]


        for pos in positions:
            ass    = pos["symbol"]
            isLong = pos["side"] == "Buy"
            qt = float(pos["size"]) * (1.0 if isLong else -1.0)
            amt= float(pos["positionValue"]) * (1.0 if isLong else -1.0)
            pnl= float(pos["unrealisedPnl"])

            # out += [[ass, qt, amt, pnl]]
            if ass not in poss:
                poss[ass] = [qt, amt, pnl]
            else:
                poss[ass][0] += qt
                poss[ass][1] += amt
                poss[ass][2] += pnl

            total_pnl += pnl
            total_exposure += abs(amt)
    
    wbs = []
    assets={}
    for cli in clis:
        wb = cli.get_wallet_balance(accountType="UNIFIED")
        wbs.append(wb)

        out = []
        asss = wb["result"]["list"][0]["coin"]
        for ass in asss:
            asset = ass["coin"]
            qt    = float(ass["walletBalance"])
            amt   = float(ass["usdValue"]) 
            out  += [[asset, qt, amt]]

            if asset not in assets:
                assets[asset] = [qt, amt]
            else:
                assets[asset][0] += qt
                assets[asset][1] += amt
            total_assets += amt
            total_margin += float(ass["totalPositionIM"])
    
    outs  = tabulate([[k, *v] for k,v in poss.items()], 
                     headers = ["Sym", "Qt", "Amnt", "Upnl"])
    outs +="\nASSETS:\n"
    outs += tabulate([[k, *v] for k,v in assets.items()], 
                     headers = ["Sym", "Qt", "Amnt"])
    outs += f"\nTOTAL EXPOSURE\t{total_exposure}\n"
    outs += f"TOTAL UPNL\t{total_pnl}\n"
    outs += f"TOTAL AVL ASSETS\t{total_assets}\n"

    print(outs)
    return ress, wbs, outs


def trade(clis: list[HTTP], ass, qt, reduce=True):
    ress = []
    for cli in clis:
        res = cli.place_order(
            category="linear", 
            symbol  =ass,
            side    ="Buy" if qt > 0.0 else "Sell",
            orderType="Market",
            qty     =abs(qt),
            reduceOnly=reduce)
        ress.append(res)
    return ress

def limit(clis, ass, qt, px):
    ress = []
    for cli in clis:
        res = cli.place_order(
            category="linear",
            symbol  =ass,
            side    ="Buy" if qt > 0.0 else "Sell",
            orderType="Limit",
            qty     =abs(qt),
            price   =px
        )
        ress.append(res)
    return ress

def trades(clis):
    
    rows = []
    for i, cli in enumerate(clis):
        res = cli.get_executions(category="linear", limit=50)
        for tr in res["result"]["list"]:
            itm = [
              i+1,
              dt.datetime.fromtimestamp(int(tr["execTime"]) // 1000), 
              tr["orderLinkId"],
              tr["side"],
              tr["execPrice"],
              tr["execQty"],
              tr["orderQty"]
            ]
            rows.append(itm)

    rows = sorted(rows, key=lambda x: x[1], reverse=True)
    tab = tabulate(rows, headers=["ids","ts", "id", "side", "px", "execQt", "origQt"])
    return tab

def close(clis):
    ress = []
    for cli in clis:
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
            
            res = trade([cli], ass, -qt, True)
            print(res)
            ress.append(res)
    return ress

def orders(clis):

    ords = []
    for i, cli in enumerate(clis):
        orders = cli.get_open_orders(
            category="linear", 
            settleCoin="USDT",
            openOnly  =0
        )
        for ord in orders["result"]["list"]:
            isLong = ord["side"] == "Buy"
            itms = [
                i+1,
                ord["symbol"],
                float(ord["leavesQty"]) * (1.0 if isLong else -1.0),
                ord["price"],
                ord["orderLinkId"]
            ]
            
            ords.append(itms)
        
    tab = tabulate(ords, headers=["AccId", "Symbol", "qt", "px", "id"])
    return tab

def cancel(clis):
    ress = []
    for cli in clis:
        res = cli.cancel_all_orders(
            category="linear",
            settleCoin="USDT"
        )
        ress.append(res)
    return ress

if __name__ == "__main__":
    args = sys.argv

    id  = args[1]

    keys = configparser.ConfigParser()
    keys.read("FutKeys.ini")
    
    clis = []
    if (id == "a"):
        id = 1
        while True:
            k = f"ACC_{id}"
            if k not in keys:
                break
            api = keys[f"ACC_{id}"]["api_key"]
            sec = keys[f"ACC_{id}"]["secret"]
            clis.append(HTTP(testnet=False, api_key=api, api_secret=sec))
            id += 1
    else:
        api = keys[f"ACC_{id}"]["api_key"]
        sec = keys[f"ACC_{id}"]["secret"]
        clis.append(HTTP(testnet=False, api_key=api, api_secret=sec))


    args[2] = args[2].lower()
    if     (args[2] == "posslim"):
        acc_info(clis)
    elif (args[2] == "trade"):
        if (len(args) < 5):
            help()
            exit(0)
        pprint(trade(clis, args[3], float(args[4]), False))
    elif (args[2] == "limit"):
        if (len(args) < 6):
            help()
            exit(0)
        pprint(limit(clis, args[3], float(args[4]), float(args[5])))
    elif (args[2] == "close"):
        close(clis)
        acc_info(clis)
    elif (args[2] == "cancel"):
        print(cancel(clis))
    elif (args[2] == "orders"):
        print(orders(clis))
    elif (args[2] == "reset"):
        cancel(clis)
        close(clis)
        acc_info(clis)
    elif (args[2] == "trades"):
        print(trades(clis))
    else:
        help()
 
