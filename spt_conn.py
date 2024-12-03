from binance.spot import Spot as Client
from pprint import pprint
import time
import sys

NO_CLOSE = ["BTC", "USDT", "BNB"]
NO_REPAY = ["ZRO", "CVX"]
KLINES   = [
    "ZROUSDT", "LEVERUSDT", "PEPEUSDT", "CVXUSDT",  "HBARUSDT",
    "KAIAUSDT","EOSUSDT",   "FXSUSDT",  "IDEXUSDT", "THEUSDT",
    "GTCUSDT", "ZKUSDT",    "CTXCUSDT", "DASHUSDT", "1MBABYDOGEUSDT",
    "MAVUSDT", "IOTAUSDT",  "CRVUSDT",  "ACTUSDT",  "SCRTUSDT",
    "XVGUSDT", "FARMUSDT",  "MLNUSDT",  "JASMYUSDT","ZRXUSDT",
    "NTRNUSDT","WUSDT",     "BLURUSDT", "FTTUSDT",  "ICPUSDT",
    "DCRUSDT", "TIAUSDT",   "NFPUSDT",  "ALPACAUSDT","BANANAUSDT",
    "SFPUSDT"
]

api_key     = []


api_secret  = []

client = None 
def mrg_info():
    res = client.margin_account()
    ua  = []
    for n in res["userAssets"]:
        if (n["netAsset"] != '0'):
            ua.append(n)

    res["userAssets"] = ua

    return res

def get_orders():
    return client.margin_open_orders()

def trade(symbol, qty):
    qty = adjToLotSz(symbol, float(qty))

    if (qty == 0.0): return
    print(f"TRADING {symbol} {qty}")
    return client.new_margin_order(
        symbol = symbol,
        side   = "BUY" if qty > 0 else "SELL",
        type   = "MARKET",
        quantity = abs(qty)
    )

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


def close_pos():
    inf = mrg_info()
    for pos in inf["userAssets"]:
        if pos["asset"] in NO_CLOSE:
            continue

        if (pos["free"] == '0'):
            continue
        print(f"Closing {pos['asset']} {pos['free']}")
        pprint(trade(pos["asset"] + "USDT", -float(pos["free"])))


def cancel_orders():
    ords = get_orders()
    for ord in ords:
        client.cancel_margin_order(symbol=ord["symbol"], origClientOrderId=ord["clientOrderId"])

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

def reset():
    cancel_orders()
    time.sleep(1.0)
    repay()
    time.sleep(1.0)
    close_pos()
    time.sleep(1.0)
    pprint(mrg_info())


def help():
    print("USAGE: [api_key_set [command+args\nreset\norders\ncancel\ntrade [symbol [qty" + 
            "\nclose\npositions\nrepay\nvol [interval\n")

if __name__ == "__main__":
    args = sys.argv
    if len(args) <= 2:
        help()
        exit()
    
    client = Client(api_key[int(args[1])-1], api_secret[int(args[1])-1])

    args[2] = args[2].lower()
    # client.borrow_repay(asset="ZRO", isIsolated="FALSE", 
    #                 symbol="ZROUSDT", amount=25.0, type="REPAY")
    if   (args[2] == "reset"):
        pprint(reset())
    elif (args[2] == "orders"):
        pprint(get_orders())
    elif (args[2] == "cancel"):
        pprint(cancel_orders())
    elif (args[2] == "trade"):
        if (len(args) < 5):
            help()
            exit(0)
        pprint(trade(args[3], float(args[4])))
    elif (args[2] == "close"):
        pprint(close_pos())
    elif (args[2] == "positions"):
        pprint(mrg_info())
    elif (args[2] == "repay"):
        pprint(repay())
    elif (args[2] == "vol"):
        if (len(args) < 4):
            help()
            exit()
        pprint(getVol(args[3]))
    else:
        help()


