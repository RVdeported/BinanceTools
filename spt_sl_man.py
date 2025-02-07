from binance.spot import Spot as Client
from pprint import pprint
import time
import sys
import re
import os
from math import ceil
import configparser
import time

CRIT_AMNT = 45000
keys = configparser.ConfigParser()
keys.read("Keys.ini")
 
CONTROL_ACCS = [1,2,3,4]
KEYS         = [(
    keys[f"ACC_{id}"]["api_key"],
    keys[f"ACC_{id}"]["secret"]) for id in CONTROL_ACCS]
CLIENTS = [Client(n[0], n[1]) for n in KEYS]
THR = 10

NO_CLOSE = ["BNB", "USDT"]

def get_amnt():
    total_amnt = 0.0
    for cli in CLIENTS:
        res = cli.margin_account()
        assets  = []

        for n in res["userAssets"]:
            if (n["netAsset"] != '0'):
                assets.append(n)

        for ass in assets:
            symb = ass["asset"]
            px = float(cli.klines(symb + "USDT", "1m", limit=1)[0][4]) \
                if symb != "USDT" else 1.0

            qt           = float(ass["netAsset"])
            amnt         = qt * px
            total_amnt  += amnt

    return total_amnt

def adjToLotSz(cli, symbol, qty, roundUp = False):
    inf = cli.exchange_info(symbol=symbol)
    px = float(cli.avg_price(symbol)["price"])
    lotSz = -1
    minNotional = -1.0
    for n in inf["symbols"][0]["filters"]:
        if n["filterType"] == "LOT_SIZE":
            lotSz = float(n["minQty"])
            
        if n["filterType"] == "NOTIONAL":
            minNotional = float(n["minNotional"])
    
    if (lotSz <= 0):
        raise Exception(f"Could not determine {symbol} lotSz")
    
    q = ceil(abs(qty) / lotSz) * lotSz
    if (roundUp):
        q = max(minNotional / px, q)
    q *= -1.0 if qty < 0 else 1.0

    
    if minNotional > abs(q) * px:
        return 0.0

    return round(q, 7)



def trade(cli, symbol, qty):
    qty = adjToLotSz(cli, symbol, float(qty))

    if (qty == 0.0): return
    print(f"TRADING {symbol} {qty}")

    args = {
        "symbol" : symbol,
        "side"   : "BUY" if qty > 0 else "SELL",
        "type"   : "MARKET",
        "quantity": abs(qty)
    }
    
    args["sideEffectType"] = "MARGIN_BUY"
    return cli.new_margin_order(**args)

def repay(cli):
    inf = cli.margin_account()
    for ass in inf["userAssets"]:
        smbl = ass["asset"] + "USDT"
        px = cli.avg_price(smbl)["price"]
        borrAmt = float(ass["borrowed"]) * px
        if (borrAmt <= THR):
            continue

        borr = float(ass["borrowed"])
        free = float(ass["free"])
        intr = float(ass["interest"])
        
        # borr -= intr
        if (free < borr + intr):
            qty = adjToLotSz(smbl, borr + intr - free, True)
            try:
                trade(cli, ass["asset"] + "USDT", qty)
            except Exception as e:
                print(e)
           
            time.sleep(1.5)
        
        borr = round(borr + intr, 9)

        print(f"Repaying {ass['asset']} int amnt {borr}")
        
        try:
            cli.borrow_repay(asset=ass["asset"], isIsolated="FALSE", 
                    symbol=ass['asset'] + "USDT", amount=borr, type="REPAY")
        except Exception as e:
            print(e)



def clear_pos():
    for cli in CLIENTS:
        repay(cli) 
        res = cli.margin_account()
         
        for pos in res["userAssets"]:
            if pos["asset"] in NO_CLOSE:
                continue
            
            amnt = float(pos["free"] - pos["borrowed"]) * 0.99

            if (amnt < THR):
                continue
            print(f"Closing {pos['asset']} {amnt}")
            try:
                pprint(trade(cli, pos["asset"] + "USDT", -amnt))
            except Exception as e:
                print(e)




if __name__ == "__main__":
    
    print(get_amnt())
    Trigg = False
    while True:
        amnt = get_amnt()
        if amnt < CRIT_AMNT:
            Trigg = True
        
        if Trigg:
            clear_pos()
        
        print(f"{amnt} / {CRIT_AMNT}")
        time.sleep(1800)


