from binance.um_futures import UMFutures as Client
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
import pandas as pd

reg = re.compile(r"PDCA::MakeOrders: Instr=([A-Z]{5,10}) Quoting Side=[a-zA-Z]{3}[\s\S].*Pos=(-{0,1}[\d]{1,6}\.{0,1}[\d]{0,10})")


def help():
    print("USAGE: [api_key_set [command+args\norders\ncancel\ntrade [symbol [qty" + 
            "\nclose\npositions\nlimit [symbol [qty [px\nposslim\ntrades [instr\n")

def get_px(cli: Client, ass):
    res = cli.book_ticker(ass)
    return float(res["askPrice"])

def acc_info(clis: list[Client]):
    poss = {}
    ress= []
    total_pnl       = 0.0
    total_assets    = 0.0
    total_exposure  = 0.0
    total_margin    = 0.0
    
    for cli in clis:
        res = cli.account()
        ress.append(res)
        positions = res["positions"]

        for pos in positions:
            ass = pos["symbol"]
            qt = float(pos["positionAmt"])
            amt= float(pos["notional"])
            pnl= float(pos["unrealizedProfit"])
            if abs(qt) <= 0.0:
                continue

            px = get_px(cli, ass)
            total_pnl += pnl
            total_exposure += abs(amt)
            
            if ass not in poss:
                poss[ass] = [qt, amt, pnl]
            else:
                poss[ass][0] += qt
                poss[ass][1] += amt
                poss[ass][2] += pnl

    # wbs = []
    assets={}
    for i, cli in enumerate(clis):
        asss = ress[i]["assets"]
        for ass in asss:
            asset = ass["asset"]
            qt    = float(ass["availableBalance"])
            if (qt <= 0.0):
                continue
            px    = 1.0 if asset == "USDT" else get_px(cli, asset + "USDT")
            amt   = px * qt
            total_assets += amt
            total_margin += float(ass["initialMargin"])
            
            if asset not in assets:
                assets[asset] = [qt, amt]
            else:
                assets[asset][0] += qt
                assets[asset][1] += amt
        
    outs  = tabulate([[k, *v] for k,v in poss.items()],
                     headers = ["Sym", "Qt", "Amnt", "Upnl"])
    outs += "\nASSETS:\n"
    outs += tabulate([[k, *v] for k,v in assets.items()], 
                     headers = ["Sym", "Qt", "Amnt"])
    outs += f"\n\nTOTAL EXPOSURE\t{total_exposure}\n"
    outs += f"TOTAL UPNL\t{total_pnl}\n"
    outs += f"TOTAL AVL ASSETS\t{total_assets}\n"
    outs += f"... WITH MARGIN\t{total_margin + total_assets}\n"

    print(outs)
    return ress, None, outs

def trade(clis, ass, qt, reduce=True):
    ress = []
    for cli in clis:
        res = cli.new_order(
           symbol   = ass,
           type     = "MARKET",
           side     = "BUY" if qt > 0.0 else "SELL",
           quantity = abs(qt),
           reduceOnly = "true" if reduce else "false"
        )
        ress.append(res)

    return ress

def limit(clis, ass, qt, px):
    ress = []
    for cli in clis:
        res = cli.new_order(
            symbol  = ass,
            type    = "LIMIT",
            timeInForce = "GTC",
            price   = px,
            side    = "BUY" if qt > 0.0 else "SELL",
            quantity= abs(qt)
        )
        ress.append(res)
    return ress

def trades(clis, instr):
    rows = []
    for i, cli in enumerate(clis):
        res = cli.get_all_orders(symbol=instr)
        for tr in res:
            itm = [
              i+1,
              dt.datetime.fromtimestamp(int(tr["updateTime"]) // 1000), 
              tr["clientOrderId"],
              tr["side"],
              tr["price"],
              tr["executedQty"],
              tr["origQty"]
            ]
            rows.append(itm)

    rows = sorted(rows, key=lambda x: x[1], reverse=True)
    tab = tabulate(rows, headers=["ids", "ts", "id", "side", "px", "execQt", "origQt"])
    return tab

def download_trades(cli):
    res = cli.get_income_history()

    instrs = set()
    for n in res:
        instrs.add(n["symbol"])

    print(instrs)

    df = pd.DataFrame(columns=["ts","instr","id","origQt","execQt","px","side"])
    for inst in instrs:
        res = cli.get_all_orders(inst)
        for n in res:
            d = {
                "instr" : inst,
                "id"    : n["clientOrderId"],
                "ts"    : int(n["updateTime"]) // 1000,
                "origQt": n["origQty"],
                "execQt": n["executedQty"],
                "px"    : n["price"],
                "side"  : n["side"]
            }
            df = pd.concat([df, pd.DataFrame([d])], ignore_index=True)
        
        df = df.sort_values(by="ts", ascending=False)
    
    
    df.to_csv("tmp.csv", index=False)
    print(df)
    


def close(clis):
    ress = []
    for cli in clis:
        acc = cli.account()
        poss = acc["positions"]
        for pos in poss:
            ass = pos["symbol"]
            qt = float(pos["positionAmt"])
            amt = float(pos["notional"])
            if abs(qt) <= 0.0:
                continue
            if (abs(amt) <= 10):
                continue
            ress.append(trade([cli], ass, -qt, True))
    return ress

def orders(clis):
    rows = []
    for i, cli in enumerate(clis):
        orders = cli.get_orders()
        for ord in orders:
            sym = ord["symbol"]
            qt  = float(ord["origQty"]) - float(ord["executedQty"])
            if (ord["side"] == "SELL"):
                qt *= -1
            px  = float(ord["price"])
            id  = ord["clientOrderId"]
            
            rows.append([i+1, id, sym, px, qt])

    
    out = tabulate(rows, headers=["AccId", "OrdId", "Instr", "Px", "Qty"])
    print(out)

    return rows

def cancel(clis):
    ress = []
    for cli in clis:
        ords = orders([cli])
        symbs = set([n[2] for n in ords])
        for sym in symbs:
            ress.append(cli.cancel_open_orders(symbol=sym))
    return ress
    
def trans(cli):
    end  = int((dt.datetime.now()).timestamp() * 1000)
    t    = int(end - 3600 * 24 * 30 * 1000)
    end -= 60000
    df = pd.DataFrame([])
    while (t < end):
        res = cli.get_income_history(limit=1000, startTime=t)
        if (len(res) < 2):
            break
        
        df = pd.concat([df, pd.DataFrame(res)])
        t = df.iloc[-1]["time"] + 1
    
    df.to_csv("trans.csv")

if __name__ == "__main__":
    args = sys.argv
    if len(args) <= 2:
        help()
        exit()
    
    id = args[1]
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
            clis.append(Client(api, sec))
            id += 1
    else:
        api = keys[f"ACC_{id}"]["api_key"]
        sec = keys[f"ACC_{id}"]["secret"]
        clis.append(Client(api, sec))


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
        print(close(clis))
        acc_info(clis)
    elif (args[2] == "cancel"):
        print(cancel(clis))
    elif (args[2] == "orders"):
        orders(clis)
    elif (args[2] == "reset"):
        print(cancel(clis))
        print(close(clis))
        acc_info(clis)
    elif (args[2] == "trades"):
        if (len(args) < 4):
            help()
            exit(1)
        print(trades(clis, args[3]))
    elif (args[2] == "dwnl"):
        download_trades(clis)
    elif (args[2] == "trans"):
        trans(clis[0])
    else:
        help()
    

