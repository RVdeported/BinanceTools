from binance.spot import Spot as Client
from pprint import pprint
import time
import sys
import re
import os
from math import ceil, floor

NO_CLOSE = ["BTC", "USDT", "BNB",  "XVG"]
NO_REPAY = []
KLINES   = [
    "ZROUSDT", "LEVERUSDT", "PEPEUSDT", "CVXUSDT",  "HBARUSDT",
    "KAIAUSDT","EOSUSDT",   "FXSUSDT",  "IDEXUSDT", "THEUSDT",
    "GTCUSDT", "ZKUSDT",    "CTXCUSDT", "DASHUSDT", "1MBABYDOGEUSDT",
    "MAVUSDT", "IOTAUSDT",  "CRVUSDT",  "ACTUSDT",  "SCRTUSDT",
    "XVGUSDT", "FARMUSDT",  "MLNUSDT",  "JASMYUSDT","ZRXUSDT",
    "NTRNUSDT","WUSDT",     "BLURUSDT", "FTTUSDT",  "ICPUSDT",
    "DCRUSDT", "TIAUSDT",   "NFPUSDT",  "ALPACAUSDT","BANANAUSDT",
    "SFPUSDT", "EOSUSDT",   "SNTUSDT",  "CAKEUSDT", "BNXUSDT",
    "SLPUSDT", "CLVUSDT",   "YFIUSDT",  "PONDUSDT", "MEMEUSDT",
    "ATOMUSDT","TLMUSDT" 
]

api_key  = [
    "eJsf2CNtp21edYLtA3diyEG39Xktuz3YxySK8IdWWbnCQPTwH1Qcg3pmfjqMYfxC",
    "6T0BVo4v8iMu0DyHiT0q0VlpC7mgPEuQSJm3qtHaEuR2qwkhIrQzcWLaUOguv6OH",
    "dBM25MkzatPe8zuQvRWleYlC6QtmbFo3ZM2z8dN94AcPZK5tddVcV8tbfOGIKsvN",
    "D3KFR4BPCX2Mb1ovakqWjsV3vrSR3XPs5FUVLQAwnJVXZmuPM9Qkd9ZuPjgNnGR2",
    "DU2WTVoCgmZPP2kK49y4RKivQjbccZrHetZzfe0CLapBrVY43vdCqvCOvJkfrhjV",
    "2ssWzeMBKoiet5KOnaP9DPPPz04quJNC0hdUmtHwzwzf0rFX0jmAZhRjAVtPAZ7k",
]


api_secret  = [
    "8WunfLKWlfqprS9NQlaOBeHtmZvcyoxBIH9dltT9we1epbp1fcSe3qZNRGz8PCqm",
    "nInIRztdCq4zoDR6183ddRc4tVFa9e8lhI0tKz9BzjloHtKlwsSsigE05TT5ejY8",
    "8vtUVpuOzhIoZUK3M8pCKK7FfwAsOQAJxBf9BrvA1l6pYHcrl7Gye8Lj6hfhCvk4",
    "a28ESzbTFRu79Aa0gnD4YhwpCGfbmNVugMT8CpVnEzjXtZpzW5G8orlrWyEusMLm",
    "yeQ23SzjJboEFfRjSEMdooIeKIJmTdL2WnulOpTfq3EvCufKE5LoWSrTeoHlcOw3",
    "4u6fxLnNeRhmsFIqxo7LYVzZ2RGpexln4gyN1wJAmgcFYUL11o9DeaLJSKUP4F0A",
]


reg = re.compile(r"PDCA::MakeOrders: Instr=([A-Z]{5,10}) Quoting Side=[a-zA-Z]{3}[\s\S].*Pos=(-{0,1}[\d]{1,6}\.{0,1}[\d]{0,10})")

PATH_LOGS = "~/Maquette/MAQUETTE-Strats/Logs/"
# PATH_LOGS = "~/log_"

MIN_POS = 6

client = None 
def mrg_info():
    res = client.margin_account()
    ua  = []
    for n in res["userAssets"]:
        if (n["netAsset"] != '0'):
            ua.append(n)

    res["userAssets"] = ua

    return res

def spt_info():
    res = client.user_asset()
    return res

def positions(id):
    assets = mrg_info()["userAssets"]

    s = 0.0
    posLog = {}
    log_name = PATH_LOGS + "pdca_" + str(id) + "\/Strat.log"
    # log_name = PATH_LOGS + "pdca" + "\/Strat.log"
    os.system(f"tail {log_name} -n 500 > tmp.txt")
    lines = open("tmp.txt", "r").readlines()
    
    for ass in assets:
        symb = ass["asset"]
        px = float(client.klines(symb + "USDT", "1m", limit=1)[0][4]) \
            if symb != "USDT" else 1.0

        qt = float(ass["netAsset"])
        amnt = qt * px
        s   += amnt
        
        actualQt = None
        for l in reversed(lines):
            match = reg.findall(l)
            if (len(match) > 0 and match[0][0] == symb + "USDT"):
                actualQt = float(match[0][1])
                break

        print(f"{symb}\t{qt}\t{round(amnt, 1)}\t{actualQt}")

    print(f"Total: {s}")
    os.remove("tmp.txt")

def _get_orders(type):
    if (type == "SPT"):
        return client.get_open_orders()
    elif (type == "MRG"):
        return client.margin_open_orders()
    else:
        raise Exception(f"INCORRECT TYPE: {type}")

def get_orders(type):
    res = _get_orders(type)
    print("Instr\tSide\tQt\tPx\tid")
    for r in res:
        print(f"{r['symbol']}\t{r['side']}\t{r['origQty']}\t"
            + f"{r['price']}\t{r['clientOrderId']}")
    return res

def trade(symbol, qty, type):
    qty = adjToLotSz(symbol, float(qty))

    if (qty == 0.0): return
    print(f"TRADING {symbol} {qty}")
    if (type not in ["SPT", "MRG"]):
        raise Exception(f"INCORRECT TRADE TYPE: {type}")

    args = {
        "symbol" : symbol,
        "side"   : "BUY" if qty > 0 else "SELL",
        "type"   : "MARKET",
        "quantity": abs(qty)
    }
    
    if (type == "SPT"):
        return client.new_order(**args)
    else:
        args["sideEffectType"] = "MARGIN_BUY"
        return client.new_margin_order(**args)

def tradeSpt(symbol, qty):
    return trade(symbol, qty, "SPT")

def tradeMrg(symbol, qty):
    return trade(symbol, qty, "MRG")


def getVol(interv):
    symbs = []
    for symb in KLINES:
        kl = client.klines(symb, interv, limit=1)
        diff = ((float(kl[0][2]) - float(kl[0][3])) / float(kl[0][1])) * 100
        symbs.append((symb, round(diff, 2)))

    symbs = sorted(symbs, reverse=True, key = lambda x: x[1])

    return symbs



def adjToLotSz(symbol, qty, roundUp = False):
    inf = client.exchange_info(symbol=symbol)
    px = float(client.avg_price(symbol)["price"])
    lotSz = -1
    minNotional = -1.0
    for n in inf["symbols"][0]["filters"]:
        if n["filterType"] == "LOT_SIZE":
            lotSz = float(n["minQty"])
            
        if n["filterType"] == "NOTIONAL":
            minNotional = float(n["minNotional"])
    
    if (lotSz <= 0):
        raise Exception(f"Could not determine {symbol} lotSz")
    
    q = abs(qty)
    if (roundUp):
        q = max(MIN_POS / px, q)   
    q = floor(q / lotSz) * lotSz

    q *= -1.0 if qty < 0 else 1.0

    
    if minNotional > abs(q) * px:
        return 0.0

    return round(q, 7)


def close_pos(type):
    if type not in ["SPT", "MRG"]: 
        raise Exception(f"INCORRECT TYPE: {type}")
    inf = mrg_info() if type == "MRG" else spt_info()
    inf = inf["userAssets"]  if type == "MRG" else inf
    for pos in inf:
        if pos["asset"] in NO_CLOSE:
            continue

        if (pos["free"] == '0'):
            continue
        print(f"Closing {pos['asset']} {pos['free']}")
        pprint(trade(pos["asset"] + "USDT", -float(pos["free"]), type))

def close_pos_spt():
    return close_pos("SPT") 

def clsoe_pos_mrg():
    return close_pos("MRG")
    

def cancel_orders(type):
    ords = get_orders(type)
    for ord in ords:
        arg_ = { "symbol"             : ord["symbol"], 
                "origClientOrderId"  : ord["clientOrderId"]}
        if (type =="SPT"):
            client.cancel_order(**arg_)
        elif (type == "MRG"):
            client.cancel_margin_order(**arg_)
        else:
            raise Exception(f"INCORRECT TYPE {type}")

def repay():
    inf = mrg_info()
    for ass in inf["userAssets"]:
        if (ass["asset"] in NO_REPAY):
            continue

        if (ass["borrowed"] == '0'):
            continue

        borr = float(ass["borrowed"])
        free = float(ass["free"])
        intr = float(ass["interest"])
        
        px = client.klines(ass["asset"] + "USDT", "1m", limit=1)[0][4]
        if ((borr + intr) * float(px) < MIN_POS):
            continue

        # borr -= intr
        if (free < borr + intr):
            smbl = ass["asset"] + "USDT"
            qty = adjToLotSz(smbl, (borr + intr - free) * 1.02, True)
            trade(ass["asset"] + "USDT", qty, "MRG")
           
            time.sleep(1.5)
        
        if (borr <= 0.000001):
            return
        borr = round(borr + intr, 8)

        print(f"Repaying {ass['asset']} int amnt {borr}")
        


        client.borrow_repay(asset=ass["asset"], isIsolated="FALSE", 
                    symbol=ass['asset'] + "USDT", amount=borr, type="REPAY")

def reset(type):
    cancel_orders(type)
    time.sleep(1.0)

    if (type == "MRG"):
        repay()
        time.sleep(1.0)
    close_pos(type)
    time.sleep(1.0)
    if (type == "SPT"):
        pprint(spt_info())
    else:
        pprint(mrg_info())

def limit(symbol, qty, px, type):
    qty = adjToLotSz(symbol, qty)
    params = {
        "symbol"        : symbol,
        "side"          : "BUY" if qty > 0 else "SELL",
        "quantity"      : abs(qty),
        "type"          : "LIMIT",
        "price"         : px,
        "timeInForce"   : "GTC"
    }
    
    if   (type == "MRG"):
        params["sideEffectType"] = "MARGIN_BUY"
        return client.new_margin_order(**params)
    elif (type == "SPT"):
        return client.new_order(**params)

    return None

def dust(symbol):
    
    return None

def help():
    print("USAGE: [api_key_set [command+args\nreset{mrg|spt}\norders{mrg|spt}\ncancel{mrg|spt}\ntrade{mrg|spt} [symbol [qty" + 
            "\nclose{mrg|spt}\npositions{mrg|spt}\nrepay\nvol [interval\nlimit{mrg|spt} [symbol [qty [px\nposslim\n")

if __name__ == "__main__":
    args = sys.argv

    if len(args) <= 2:
        help()
        exit()


    client = Client(api_key[int(args[1])-1], api_secret[int(args[1])-1])
    # client.borrow_repay(asset="AMP", isIsolated="FALSE", 
    #                 symbol="AMPUSDT", amount=9200, type="REPAY")
    # exit(0) 
    args[2] = args[2].lower()
    # client.borrow_repay(asset="ZRO", isIsolated="FALSE", 
    #                 symbol="ZROUSDT", amount=25.0, type="REPAY")


    if   (args[2] == "resetspt"):
        pprint(reset("SPT"))
    elif   (args[2] == "resetmrg"):
        pprint(reset("MRG"))
    elif (args[2] == "ordersspt"):
        get_orders("SPT")
    elif (args[2] == "ordersmrg"):
        get_orders("MRG")
    elif (args[2] == "cancelspt"):
        pprint(cancel_orders("SPT"))
    elif (args[2] == "cancelmrg"):
        pprint(cancel_orders("MRG"))
    elif (args[2] == "tradespt"):
        if (len(args) < 5):
            help()
            exit(0)
        pprint(tradeSpt(args[3], float(args[4])))
    elif (args[2] == "trademrg"):
        if (len(args) < 5):
            help()
            exit(0)
        pprint(tradeMrg(args[3], float(args[4])))
    elif (args[2] == "closespt"):
        pprint(close_pos("SPT"))
    elif (args[2] == "closemrg"):
        pprint(close_pos("MRG"))
    elif (args[2] == "positions"):
        pprint(mrg_info())
        pprint(spt_info())
    elif (args[2] == "repay"):
        pprint(repay())
    elif (args[2] == "vol"):
        if (len(args) < 4):
            help()
            exit()
        pprint(getVol(args[3]))
    elif (args[2][:5] == "limit"):
        if (len(args) < 6):
            help()
            exit(0)
        pprint(limit(args[3], float(args[4]), float(args[5]), args[2][-3:].upper()))
    elif (args[2] == "posslim"):
        positions(int(args[1]))
    else:
        help()


