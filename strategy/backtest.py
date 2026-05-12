import ccxt
import pandas as pd
import vectorbt as vbt

from strategy.indicators import apply_indicators
from strategy.signals import generate_signal
from strategy.utils import clean_dataframe

exchange = ccxt.delta()


def fetch_data():

    bars = exchange.fetch_ohlcv(
        'BTC/USDT',
        timeframe='15m',
        limit=10000
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


df = fetch_data()

df = apply_indicators(df)

df = clean_dataframe(df)

signals = []

for i in range(200, len(df)):

    temp_df = df.iloc[:i]

    signal_data = generate_signal(temp_df)

    signals.append(
        signal_data['signal']
    )

signals = (
    ['HOLD'] * 200
    + signals
)

entries = (
    pd.Series(signals, index=df.index)
    == 'BUY'
)

short_entries = (
    pd.Series(signals, index=df.index)
    == 'SELL'
)

sl_stop = (( df['atr'] * 1.5 ) / df['close'])

pf = vbt.Portfolio.from_signals(
    close=df['close'],
    entries=entries,
    short_entries=short_entries,

    sl_stop=sl_stop,
    sl_trail=True,
    fees=0.001,
    slippage=0.0005,
    init_cash=10_000
)

print(
    pf.stats()
)

pf.plot().show()
