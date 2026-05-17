PAPER_TRADING = False

import ccxt
import os
from dotenv import load_dotenv
from strategy.config import LIVE_TRADING

load_dotenv()

exchange = ccxt.delta({
    "apiKey": os.getenv("DELTA_API_KEY"),
    "secret": os.getenv("DELTA_API_SECRET"),
    "enableRateLimit": True
})
exchange.set_sandbox_mode(True)

def place_order(signal_data, pair):

    print("PLACE_ORDER FUNCTION CALLED")

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
