from acc_info import client, get_positions
from pprint import pprint
import sys

instrs = ["BTCUSDT", "ETHUSDT", "DOGEUSDT", "MATICUSDT", "LINKUSDT",
          "BNBUSDT", "XRPUSDT", "SOLUSDT",  "FILUSDT"]
def display_help():
    print("Closes all positions at Market and cancels all open orders in the instrs listed below:")
    print(" ".join(instrs))
    print("No prams needed")

def close_positions():
    assets, _ = get_positions()
    for pos in assets:
        symbol = pos["symbol"]
        side   = "SELL" if float(pos["notional"]) > 0 else "BUY"
        qty    = abs(float(pos["positionAmt"]))
        response = client.new_order(
            symbol=symbol,
            side=side,
            type="MARKET",
            quantity=qty
        )
        pprint(response)
    for instr in instrs:
        pprint(client.cancel_open_orders(instr))

if __name__ == "__main__":
    if "--help" in sys.argv:
        display_help()
        exit(1)

    close_positions()
