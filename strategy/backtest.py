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
        timeframe='1h',
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
    print(f"Fetched candles: {len(df)}")

    return df


df = fetch_data()

df = apply_indicators(df)

df = clean_dataframe(df)

signals = []

last_trade_index = -12

for i in range(200, len(df)):

    # Cooldown period
    if i - last_trade_index < 12:

        signals.append("HOLD")

        continue

    temp_df = df.iloc[:i]

    signal_data = generate_signal(temp_df)

    signals.append(
        signal_data['signal']
    )

    # Update last trade time
    if signal_data['signal'] == "BUY":

        last_trade_index = i
        
    missing_signals = ( len(df.index) - len(signals) - 1)
    signals = ( 
        ['HOLD'] * missing_signals + signals 
    )
    entries = (
        pd.Series(signals, index=df.index) == 'BUY'
    )
sl_stop = (( df['atr'] * 1.5 ) / df['close'])

pf = vbt.Portfolio.from_signals(

    close=df['close'],

    entries=entries,

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
