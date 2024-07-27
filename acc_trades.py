from acc_info import client
from pprint import pprint
from datetime import datetime as dt
from termcolor import colored
import sys


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Enter symbol!")
        exit()
    
    res = client.get_account_trades(symbol=sys.argv[1], recWindow=6000)
    res = sorted(res, reverse=True, key=lambda x: x["time"])


    for n in res:
        t = dt.fromtimestamp(n["time"] / 1000)
        print(colored("{}:\tPx:{}\tqty:{}\ttime:{}\tmaker:{}".format(
            n["symbol"], n["price"], n["qty"], t.strftime("%d.%m.%Y, %H:%M:%S"), n["maker"])
            , "green" if n["buyer"] else "yellow"))
