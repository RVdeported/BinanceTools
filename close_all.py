from acc_info import clientCM, clientUM, get_positions
from pprint import pprint
import sys

instrsUM = ["BTCUSDT", "ETHUSDT", "DOGEUSDT", "MATICUSDT", "LINKUSDT",
          "BNBUSDT", "XRPUSDT", "SOLUSDT",  "FILUSDT"]

instrsCM = ["BTCUSD_PERP", "ETHUSD_PERP", "DOGEUSD_PERP", 
            "MATICUSD_PERP", "LINKUSD_PERP",
            "BNBUSD_PERP", "XRPUSD_PERP", "SOLUSD_PERP",  "FILUSD_PERP"]


def display_help():
    print("Closes all positions at Market and cancels all open orders in the instrs listed below:")
    print(" ".join(instrsCM))
    print("PARAMS: [{um|cm}")

def close_positions(UM):
    assets, _ = get_positions(UM)
    client = clientUM if UM else clientCM
    instrs = []
    for pos in assets:
        symbol = pos["symbol"]
        side   = "SELL" if float(pos["positionAmt"]) > 0 else "BUY"
        qty    = abs(float(pos["positionAmt"]))
        if (qty > 0):
            instrs.append(symbol)
            try:
                response = client.new_order(
                    symbol=symbol,
                    side=side,
                    type="MARKET",
                    quantity=qty)
                pprint(response)
            except Exception as e:
                print(e)
        
    for instr in instrs:
        pprint(client.cancel_open_orders(instr))

if __name__ == "__main__":
    if "--help" in sys.argv or len(sys.argv) != 2:
        display_help()
        exit(1)
    
    UM = sys.argv[1] == "um" if len(sys.argv) > 1 else True

    close_positions(UM)
