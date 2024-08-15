from acc_info import clientCM, clientUM, INSTR_PRICE
import sys
import datetime as dt


def display_help():
    print("Prints income for a specified preceeded hours")
    print("PARAMS: [{cm|um} [hours")
if __name__ == "__main__":
    if ("--help" in sys.argv or len(sys.argv) != 3):
        display_help()
        exit(0)

    if (sys.argv[1] not in ["um", "cm"]):
        display_help()
        exit(1)


    UM = sys.argv[1] == "um"
    client = clientUM if UM else clientCM
    
    hours = int(sys.argv[2])
    startTs = dt.datetime.now() - dt.timedelta(hours=hours)
    res = client.get_income_history(startTime=int(startTs.timestamp() * 1000), limit=1000)
    
    income = 0
    for n in res:
        income += float(n["income"]) * INSTR_PRICE[n["asset"]]

    print(f"Total income starting from {startTs.timestamp()} is {income}")


