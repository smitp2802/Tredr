"""Live trading loop for Tredr.

Usage:
    venv/bin/python -m strategy.main BTC/USD:USD
"""
import sys
import time

import pandas as pd
from dotenv import load_dotenv

from strategy.config import (
    DEFAULT_PAIR,
    DEFAULT_TIMEFRAME,
    DEFAULT_LOOKBACK,
    get_settings,
)
from strategy.indicators import apply_indicators
from strategy.signals import generate_signal
from strategy.execution import get_exchange, fetch_usd_balance, place_order
from strategy.journal import log_trade
from strategy.utils import clean_dataframe

load_dotenv()


def fetch_data(exchange, pair, timeframe, lookback):
    """Fetch OHLCV data from Delta."""
    bars = exchange.fetch_ohlcv(
        pair,
        timeframe=timeframe,
        limit=lookback,
    )
    df = pd.DataFrame(
        bars,
        columns=["timestamp", "open", "high", "low", "close", "volume"],
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    return df


def main(pair=None):
    pair = pair or (sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PAIR)
    settings = get_settings(pair)

    print("=" * 50)
    print("PAIR:", pair)
    print("TIMEFRAME:", DEFAULT_TIMEFRAME)
    print("LOOKBACK:", DEFAULT_LOOKBACK)
    print("SETTINGS:", settings)
    print("=" * 50)

    exchange = get_exchange()
    exchange.load_markets()

    try:
        usd = fetch_usd_balance()
        print("USD Balance:", usd)
    except Exception as e:
        print("Balance check failed:", e)

    in_position = False
    last_timestamp = None

    while True:
        try:
            df = fetch_data(exchange, pair, DEFAULT_TIMEFRAME, DEFAULT_LOOKBACK)
        except Exception as e:
            print("DATA FETCH FAILED:", e)
            time.sleep(60)
            continue

        df = apply_indicators(df)
        df = clean_dataframe(df)

        signal_data = generate_signal(df, settings=settings)

        if signal_data["timestamp"] == last_timestamp:
            time.sleep(60)
            continue

        last_timestamp = signal_data["timestamp"]
        print(f"New candle: {last_timestamp}")
        print(signal_data)

        log_trade(signal_data)

        if signal_data["signal"] == "BUY" and not in_position:
            place_order(signal_data, pair, settings=settings)
            in_position = True

        elif signal_data["signal"] == "SELL" and in_position:
            place_order(signal_data, pair, settings=settings)
            in_position = False

        time.sleep(60)


if __name__ == "__main__":
    main()
