from acc_info import clientCM, clientUM
import sys
from pprint import pprint

def display_help():
    print("Trades at Market price")
    print("PARAMS: [{um|cm} [symbol [side{0: SELL, 1: BUY} [qty")

if __name__ == "__main__":
    if ("--help" in sys.argv or len(sys.argv) != 5):
        display_help()
        exit(0)
   
    UM = sys.argv[1] == "um" if len(sys.argv) > 1 else True
    client = clientUM if UM else clientCM

    
    response = client.new_order(
        symbol=sys.argv[2],
        side="SELL" if sys.argv[3] == "0" else "BUY",
        type="MARKET",
        quantity=float(sys.argv[4]),
    )
    pprint(response)
