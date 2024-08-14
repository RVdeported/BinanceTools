from acc_info import clientUM, clientCM
from pprint import pprint
from datetime import datetime as dt
from termcolor import colored
import sys


def display_help():
    print("Displays last 100 trades for a symblo")
    print("PRAMS: [{um|cm} [Symbol")

if __name__ == "__main__":
    if "--help" in sys.argv:
        display_help()
        exit(0)
    
    if (len(sys.argv) > 1 and sys.argv[1] not in ["um", "cm"]):
        display_help()
        exit(1)

    if len(sys.argv) != 3:
        print("Enter symbol!")
        exit(1)
    
    UM = sys.argv[1] == "um" if len(sys.argv) > 1 else True
    client = clientUM if UM else clientCM

    res = client.get_all_orders(symbol=sys.argv[2], recWindow=6000, limit=100)
    res = sorted(res, reverse=True, key=lambda x: x["time"])


    for n in res:
        if n["status"] != "FILLED":
            continue
        t = dt.fromtimestamp(n["time"] / 1000)
        print(colored("{}:  Px:{}\tqty:{}\ttime:{}\tReqID:{}".format(
            n["symbol"], n["avgPrice"], n["executedQty"], t.strftime("%d.%m.%Y, %H:%M:%S.%f"), 
            n["clientOrderId"])
            , "green" if n["side"]=="BUY" else "yellow"))
