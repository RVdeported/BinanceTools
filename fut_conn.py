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

reg = re.compile(r"PDCA::MakeOrders: Instr=([A-Z]{5,10}) Quoting Side=[a-zA-Z]{3}[\s\S].*Pos=(-{0,1}[\d]{1,6}\.{0,1}[\d]{0,10})")


def help():
    print("USAGE: [api_key_set [command+args\norders\ncancel\ntrade [symbol [qty" + 
            "\nclose\npositions\nlimit [symbol [qty [px\nposslim\ntrades [instr\n")

def get_px(cli: Client, ass):
    res = cli.book_ticker(ass)
    return float(res["askPrice"])

def acc_info(cli: Client):
    res = cli.account()
    positions = res["positions"]
    out = [["Instr", "Qt", "Amn", "tupnl"]]

    total_pnl       = 0.0
    total_assets    = 0.0
    total_exposure  = 0.0
    total_margin    = 0.0
    for pos in positions:
        ass = pos["symbol"]
        qt = float(pos["positionAmt"])
        amt= float(pos["notional"])
        pnl= float(pos["unrealizedProfit"])
        if abs(qt) <= 0.0:
            continue

        px = get_px(cli, ass)
        out += [[ass, qt, amt, pnl]]
        total_pnl += pnl
        total_exposure += abs(amt)
    
    print(tabulate(out))
    print("\nASSETS:\n")
    out = []
    assets = res["assets"]
    for ass in assets:
        asset = ass["asset"]
        qt    = float(ass["availableBalance"])
        if (qt <= 0.0):
            continue
        px    = 1.0 if asset == "USDT" else get_px(cli, asset + "USDT")
        amt   = px * qt
        out  += [[asset, qt, amt]]
        total_assets += amt
        total_margin += float(ass["initialMargin"])
    
    print(tabulate(out))
    print(f"TOTAL EXPOSURE\t{total_exposure}")
    print(f"TOTAL UPNL\t{total_pnl}")
    print(f"TOTAL AVL ASSETS\t{total_assets}")
    print(f"... WITH MARGIN\t{total_margin + total_assets}")

def trade(cli, ass, qt, reduce=True):
    res = cli.new_order(
       symbol   = ass,
       type     = "MARKET",
       side     = "BUY" if qt > 0.0 else "SELL",
       quantity = abs(qt),
       reduceOnly = "true" if reduce else "false"
    )

    return res

def limit(cli, ass, qt, px):
    res = cli.new_order(
        symbol  = ass,
        type    = "LIMIT",
        timeInForce = "GTC",
        price   = px,
        side    = "BUY" if qt > 0.0 else "SELL",
        quantity= abs(qt)
    )
    return res

def trades(cli, instr):
    res = cli.get_all_orders(symbol=instr)
    rows = []
    for tr in res:
        itm = [
          dt.datetime.fromtimestamp(int(tr["updateTime"]) // 1000), 
          tr["clientOrderId"],
          tr["price"],
          tr["executedQty"],
          tr["origQty"]
        ]
        rows.append(itm)

    rows = sorted(rows, key=lambda x: x[0], reverse=True)
    tab = tabulate(rows, headers=["ts", "id", "px", "execQt", "origQt"])
    return tab

def close(cli):
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
        
        print(trade(cli, ass, -qt, True))

def orders(cli):
    orders = cli.get_orders()
    out = "Symbol\tqt\tpx\tid\n"
    ords = []
    for ord in orders:
        sym = ord["symbol"]
        qt  = float(ord["origQty"]) - float(ord["executedQty"])
        if (ord["side"] == "SELL"):
            qt *= -1
        px  = float(ord["price"])
        id  = ord["clientOrderId"]
        
        ords.append({
            "px": px,
            "qt": qt,
            "sym": sym})

        out += f"{sym}\t{qt}\t{px}\t{id}\n"
        
    print(out)

    return ords

def cancel(cli):
    ords = orders(cli)
    symbs = set([n["sym"] for n in ords])
    for sym in symbs:
        print(cli.cancel_open_orders(symbol=sym))


if __name__ == "__main__":
    args = sys.argv
    if len(args) <= 2:
        help()
        exit()
    
    id = int(args[1])
    keys = configparser.ConfigParser()
    keys.read("FutKeys.ini")
    api = keys[f"ACC_{id}"]["api_key"]
    sec = keys[f"ACC_{id}"]["secret"]

    client = Client(api, sec)
    
    args[2] = args[2].lower()
    if     (args[2] == "posslim"):
        acc_info(client)
    elif (args[2] == "trade"):
        if (len(args) < 5):
            help()
            exit(0)
        pprint(trade(client, args[3], float(args[4])))
    elif (args[2] == "limit"):
        if (len(args) < 6):
            help()
            exit(0)
        pprint(limit(client, args[3], float(args[4]), float(args[5])))
    elif (args[2] == "close"):
        close(client)
        acc_info(client)
    elif (args[2] == "cancel"):
        cancel(client)
    elif (args[2] == "orders"):
        orders(client)
    elif (args[2] == "reset"):
        cancel(client)
        close(client)
        acc_info(client)
    elif (args[2] == "trades"):
        if (len(args) < 4):
            help()
            exit(1)
        print(trades(client, args[3]))
    else:
        help()
    

