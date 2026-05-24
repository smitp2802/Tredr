PAPER_TRADING = False

import ccxt
import os
from dotenv import load_dotenv
from strategy.config import LIVE_TRADING
from strategy.config import SETTINGS

load_dotenv()
print("API KEY =", os.getenv("DELTA_API_KEY"))

exchange = ccxt.delta({
    "apiKey": os.getenv("DELTA_API_KEY"),
    "secret": os.getenv("DELTA_API_SECRET"),
    "enableRateLimit": True
})

exchange.urls["api"] = {
    "public": "https://cdn-ind.testnet.deltaex.org",
    "private": "https://cdn-ind.testnet.deltaex.org",
}

exchange.load_markets()


print("Contract Size:", market["contractSize"])
print("Min Amount:", market["limits"]["amount"]["min"])

try:
    balance = exchange.fetch_balance()

    print(
        "USD Balance:",
        balance["total"].get("USD", 0)
    )

except Exception as e:
    print("Balance check failed")
    print(e)
    
def place_order(signal_data, pair):
    
    market = exchange.market(pair)
    print("PLACE_ORDER FUNCTION CALLED")

    balance = exchange.fetch_balance()
    usd_balance = balance["total"].get("USD", 0)
    risk_amount = usd_balance * SETTINGS["RISK_PER_TRADE"]

    print(f"LIVE_TRADING = {LIVE_TRADING}")

    signal = signal_data['signal']

    print(f"SIGNAL RECEIVED: {signal}")

    if not LIVE_TRADING:
        print("LIVE TRADING DISABLED")
        return

    try:

        if signal == "BUY":

            print("SENDING BUY ORDER TO DELTA")

            order = exchange.create_market_buy_order(
                pair, 1
            )

            print("ORDER SUCCESS")

            print(order)

    except Exception as e:

        print("ORDER FAILED")

        print(e)

    print(
        f"""
        =========================
        SIGNAL: {signal}
        PAIR: {pair}
        PRICE: {signal_data['price']}
        SCORE LONG: {signal_data['score_long']}
        RSI: {signal_data['rsi']}
        ADX: {signal_data['adx']}
        TIME: {signal_data['timestamp']}
        =========================
        """
    )

    with open("trade_log.txt", "a") as f:
        f.write(
            f"{signal_data['timestamp']} | "
            f"{pair} | "
            f"{signal_data['signal']} | "
            f"{signal_data['price']}\n"
        )
