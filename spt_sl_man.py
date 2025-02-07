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

def clear_pos():
    pass


if __name__ == "__main__":
    
    print(get_amnt())
    # Trigg = False
    # while True:
    #     amnt = get_amnt()
    #     if amnt > CRIT_AMNT:
    #         Trigg = True
    #     
    #
    #
    #
    #     if Trigg:
    #         clear_pos()
    #
    #
    #     time.sleep(1800)


