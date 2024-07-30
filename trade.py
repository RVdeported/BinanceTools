from acc_info import client
import sys
from pprint import pprint

def display_help():
    print("Trades at Market price")
    print("PARAMS: [symbol [side{0: SELL, 1: BUY} [qty")

if __name__ == "__main__":
    if ("--help" in sys.argv or len(sys.argv) != 4):
        display_help()
        exit(0)

    response = client.new_order(
        symbol=sys.argv[1],
        side="SELL" if sys.argv[2] == "0" else "BUY",
        type="MARKET",
        quantity=float(sys.argv[3]),
    )
    pprint(response)
