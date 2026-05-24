import ccxt
import pandas as pd
import sys
import time
from strategy.config import (
    PAIR_CONFIGS,
    TIMEFRAME,
    LOOKBACK
)
PAIR = sys.argv[1]

SETTINGS = PAIR_CONFIGS[PAIR]

print("=" * 50)
print("PAIR:", PAIR)
print("TIMEFRAME:", TIMEFRAME)
print("LOOKBACK:", LOOKBACK)
print("SETTINGS:", SETTINGS)
print("=" * 50)

try:
    balance = exchange.fetch_balance()

    print(
        "USD Balance:",
        balance["total"].get("USD", 0)
    )

except Exception as e:

    print("Balance check failed")

    print(e)

from strategy.indicators import apply_indicators
from strategy.signals import generate_signal
from strategy.execution import place_order
from strategy.journal import log_trade
from strategy.utils import clean_dataframe
from strategy.config import TIMEFRAME, LOOKBACK

exchange = ccxt.delta()

def fetch_data():

    bars = exchange.fetch_ohlcv(
        PAIR,
        timeframe=TIMEFRAME,
        limit=LOOKBACK
    )

    df = pd.DataFrame(
        bars,
        columns=[
            'timestamp',
            'open',
            'high',
            'low',
            'close',
            'volume'
        ]
    )

    df['timestamp'] = pd.to_datetime(
        df['timestamp'],
        unit='ms'
    )

    df.set_index(
        'timestamp',
        inplace=True
    )

    return df

#try:
#
#    exchange.load_markets()
#
#    if PAIR not in exchange.symbols:
#
#        print(f"PAIR NOT FOUND: {PAIR}")
#
#        sys.exit(1)
#
#    print(f"PAIR VERIFIED: {PAIR}")

#except Exception as e:

#    print("MARKET CHECK FAILED")

#    print(e)

#    sys.exit(1)
    

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

        if signal_data['timestamp'] == last_timestamp:

            time.sleep(60)

            continue

        last_timestamp = signal_data['timestamp']
        print(f"Waiting... Current candle: {last_timestamp}")

        print(signal_data)

        log_trade(signal_data)

        if signal_data['signal'] == "BUY" and not in_position:

            place_order(signal_data, PAIR)

            in_position = True

        elif signal_data['signal'] == "SELL":

            in_position = False

        time.sleep(60)


if __name__ == "__main__":

    main()

