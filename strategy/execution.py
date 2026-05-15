PAPER_TRADING = False

import ccxt
import os

from dotenv import load_dotenv

load_dotenv()

exchange = ccxt.delta({
    "apiKey": os.getenv("DELTA_API_KEY"),
    "secret": os.getenv("DELTA_API_SECRET"),
    "enableRateLimit": True
})

order = exchange.create_market_buy_order(
    PAIR,
    1 #Quantity
)

print(order)

def place_order(signal_data, pair):

    signal = signal_data['signal']

    if signal == "BUY":

        if PAPER_TRADING:
            print(f"[PAPER] BUY {pair}")

        else:
            exchange.create_market_buy_order(...)


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
