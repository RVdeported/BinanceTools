from binance.spot import Spot as Client
from pprint import pprint
import time
import sys

NO_CLOSE = ["BTC", "USDT", "BNB", "ETH"]
NO_REPAY = ["ZRO", "CVX"]
KLINES   = [
    "ZROUSDT", "LEVERUSDT", "PEPEUSDT", "CVXUSDT",  "HBARUSDT",
    "KAIAUSDT","EOSUSDT",   "FXSUSDT",  "IDEXUSDT", "THEUSDT",
    "GTCUSDT", "ZKUSDT",    "CTXCUSDT", "DASHUSDT", "1MBABYDOGEUSDT",
    "MAVUSDT", "IOTAUSDT",  "CRVUSDT",  "ACTUSDT",  "SCRTUSDT",
    "XVGUSDT", "FARMUSDT",  "MLNUSDT",  "JASMYUSDT","ZRXUSDT",
    "NTRNUSDT","WUSDT",     "BLURUSDT", "FTTUSDT",  "ICPUSDT",
    "DCRUSDT", "TIAUSDT",   "NFPUSDT",  "ALPACAUSDT","BANANAUSDT",
    "SFPUSDT", "EOSUSDT"
]

api_key     = [
]

api_secret  = [
]

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

def get_orders(type):
    if (type == "SPT"):
        return client.open_orders()
    elif (type == "MRG"):
        return client.margin_open_orders()
    else:
        raise Exception(f"INCORRECT TYPE: {type}")


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



def adjToLotSz(symbol, qty):
    inf = client.exchange_info(symbol=symbol)
    lotSz = -1
    minNotional = -1.0
    for n in inf["symbols"][0]["filters"]:
        if n["filterType"] == "LOT_SIZE":
            lotSz = float(n["minQty"])
            
        if n["filterType"] == "NOTIONAL":
            minNotional = float(n["minNotional"])
    
    if (lotSz <= 0):
        raise Exception(f"Could not determine {symbol} lotSz")
    
    q = (abs(qty) // lotSz) * lotSz
    q *= -1.0 if qty < 0 else 1.0

    px = float(client.avg_price(symbol)["price"])
    if minNotional > abs(q) * px:
        return 0.0

    return round(q, 5)


def close_pos(type):
    if type not in ["SPT", "MRG"]: 
        raise Exception(f"INCORRECT TYPE: {type}")
    inf = mrg_info() if type == "MRG" else spt_info()
    assets = inf["userAssets"]  if type == "MRG" else inf
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
        arg = { "symbol"             : ord["symbol"], 
                "origClientOrderId"  : ord["clientOrderId"]}
        if (type =="SPT"):
            client.cancel_order(*arg)
        elif (type == "MRG"):
            client.cancel_margin_order(*arg)
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
        
        # borr -= intr
        if (free < borr):
            smbl = ass["asset"] + "USDT"
            qty = adjToLotSz(smbl, borr - free)
            trade(ass["asset"] + "USDT", qty)
           
            time.sleep(1.5)
        
        if (borr <= 0.000001):
            return
        borr = round(borr * 0.98, 4)

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


def help():
    print("USAGE: [api_key_set [command+args\nreset{mrg|spt}\norders{mrg|spt}\ncancel{mrg|spt}\ntrade{mrg|spt} [symbol [qty" + 
            "\nclose{mrg|spt}\npositions{mrg|spt}\nrepay\nvol [interval\n")

if __name__ == "__main__":
    args = sys.argv
    if len(args) <= 2:
        help()
        exit()
    
    client = Client(api_key[int(args[1])-1], api_secret[int(args[1])-1])

    args[2] = args[2].lower()
    # client.borrow_repay(asset="ZRO", isIsolated="FALSE", 
    #                 symbol="ZROUSDT", amount=25.0, type="REPAY")
    if   (args[2] == "resetspt"):
        pprint(reset("SPT"))
    elif   (args[2] == "resetmrg"):
        pprint(reset("MRG"))
    elif (args[2] == "ordersspt"):
        pprint(get_orders("SPT"))
    elif (args[2] == "ordersmrg"):
        pprint(get_orders("MRG"))
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
    else:
        help()


