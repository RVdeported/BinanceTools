from acc_info import client
from pprint import pprint
from datetime import datetime as dt
from termcolor import colored
import sys


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Enter symbol!")
        exit()
    
    res = client.get_all_orders(symbol=sys.argv[1], recWindow=6000, limit=100)
    res = sorted(res, reverse=True, key=lambda x: x["time"])


    for n in res:
        if n["status"] != "FILLED":
            continue
        t = dt.fromtimestamp(n["time"] / 1000)
        print(colored("{}:  Px:{}\tqty:{}\ttime:{}\tReqID:{}".format(
            n["symbol"], n["avgPrice"], n["executedQty"], t.strftime("%d.%m.%Y, %H:%M:%S.%f"), 
            n["clientOrderId"])
            , "green" if n["side"]=="BUY" else "yellow"))
