from acc_info import client
import sys
from pprint import pprint

def display_help():
    print("[symbol [side{0: SELL, 1: BUY} [qty")

if __name__ == "__main__":
    if (len(sys.argv) != 4):
        display_help()
        exit()

    response = client.new_order(
        symbol=sys.argv[1],
        side="SELL" if sys.argv[2] == "0" else "BUY",
        type="MARKET",
        quantity=float(sys.argv[3]),
    )
    pprint(response)
