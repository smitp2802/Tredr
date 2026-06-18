import ccxt
import pandas as pd
import sys
import time
import os

from dotenv import load_dotenv

from strategy.config import (
    PAIR_CONFIGS,
    TIMEFRAME,
    LOOKBACK
)

from strategy.indicators import apply_indicators
from strategy.signals import generate_signal
from strategy.execution import place_order
from strategy.journal import log_trade
from strategy.utils import clean_dataframe

# ==========================================
# CONFIG
# ==========================================

PAIR = sys.argv[1]

SETTINGS = PAIR_CONFIGS[PAIR]

print("=" * 50)
print("PAIR:", PAIR)
print("TIMEFRAME:", TIMEFRAME)
print("LOOKBACK:", LOOKBACK)
print("SETTINGS:", SETTINGS)
print("=" * 50)

# ==========================================
# DELTA CONNECTION
# ==========================================

load_dotenv()

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

# ==========================================
# BALANCE CHECK
# ==========================================

try:

    balance = exchange.fetch_balance()

    print(
        "USD Balance:",
        balance["total"].get("USD", 0)
    )

except Exception as e:

    print("Balance check failed")
    print(e)

# ==========================================
# DATA FETCH
# ==========================================

def fetch_data():

    bars = exchange.fetch_ohlcv(
        PAIR,
        timeframe=TIMEFRAME,
        limit=LOOKBACK
    )

    df = pd.DataFrame(
        bars,
        columns=[
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume"
        ]
    )

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        unit="ms"
    )

    df.set_index(
        "timestamp",
        inplace=True
    )

    return df

# ==========================================
# MAIN LOOP
# ==========================================

def main():

    in_position = False
    last_timestamp = None

    while True:

        try:

            df = fetch_data()

        except Exception as e:

            print("DATA FETCH FAILED!!")
            print(e)

            time.sleep(60)

            continue

        df = apply_indicators(df)

        df = clean_dataframe(df)

        signal_data = generate_signal(df)

        if signal_data["timestamp"] == last_timestamp:

            time.sleep(60)

            continue

        last_timestamp = signal_data["timestamp"]

        print(
            f"Waiting... Current candle: {last_timestamp}"
        )

        print(signal_data)

        log_trade(signal_data)

        if signal_data["signal"] == "BUY" and not in_position:

            place_order(
                signal_data,
                PAIR
            )

            in_position = True

        elif signal_data["signal"] == "SELL" and in_position:
            # Close the open long position
            place_order(
                signal_data,
                PAIR
            )

            in_position = False

        time.sleep(60)

# ==========================================
# ENTRY
# ==========================================

if __name__ == "__main__":
    main()
