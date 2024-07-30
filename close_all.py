from acc_info import client, get_positions
from pprint import pprint

instrs = ["BTCUSDT", "ETHUSDT", "DOGEUSDT", "MATICUSDT", "LINKUSDT",
          "BNBUSDT", "XRPUSDT", "SOLUSDT",  "FILUSDT"]

def close_positions():
    assets, acc_info = get_positions()
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
    close_positions()
