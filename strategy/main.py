import ccxt
import pandas as pd

from config import (
    PAIR,
    TIMEFRAME,
    LOOKBACK
)

from indicators import apply_indicators
from signals import generate_signal
from execution import place_order
from journal import log_trade
from utils import clean_dataframe

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


def main():

    df = fetch_data()

    df = apply_indicators(df)

    df = clean_dataframe(df)

    signal_data = generate_signal(df)

    print(signal_data)

    log_trade(signal_data)

    if signal_data['signal'] != 'HOLD':

        place_order(signal_data)


if __name__ == '__main__':

    main()
