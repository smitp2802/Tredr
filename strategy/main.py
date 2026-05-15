import ccxt
import pandas as pd

from strategy.config import PAIR_CONFIGS
PAIR = sys.argv[1]

SETTINGS = PAIR_CONFIGS[PAIR]

from strategy.indicators import apply_indicators
from strategy.signals import generate_signal
from strategy.execution import place_order
from strategy.journal import log_trade
from strategy.utils import clean_dataframe

exchange = ccxt.delta()


def fetch_data():

    bars = exchange.fetch_ohlcv(
        PAIR,
        timeframe=SETTINGS["TIMEFRAME"],
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
