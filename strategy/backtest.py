import ccxt
import pandas as pd
import vectorbt as vbt

from strategy.config import SETTINGS, PAIR
from strategy.indicators import apply_indicators
from strategy.signals import generate_signal
from strategy.utils import clean_dataframe

exchange = ccxt.delta()


def fetch_data():

    # 1H DATA
    bars_1h = exchange.fetch_ohlcv(
        
        PAIR.replace("USDT", "/USDT"),
        
        timeframe='1h',
        limit=10000
    )

    df_1h = pd.DataFrame( 
        bars_1h, columns=['timestamp','open','high','low','close','volume']
    )

    df_1h['timestamp'] = pd.to_datetime(
        df_1h['timestamp'],
        unit='ms'
    )

    df_1h.set_index(
        'timestamp',
        inplace=True
    )

    # 4H DATA
    bars_4h = exchange.fetch_ohlcv(
        'BTC/USDT',
        timeframe='4h',
        limit=3000
    )

    df_4h = pd.DataFrame(
        bars_4h,
        columns=[
            'timestamp',
            'open',
            'high',
            'low',
            'close',
            'volume'
        ]
    )

    df_4h['timestamp'] = pd.to_datetime(
        df_4h['timestamp'],
        unit='ms'
    )

    df_4h.set_index(
        'timestamp',
        inplace=True
    )

    # APPLY INDICATORS
    df_1h = apply_indicators(df_1h)
    df_4h = apply_indicators(df_4h)

    # HTF TREND
    df_4h['htf_bullish'] = (
        df_4h['ema20'] >
        df_4h['ema50']
    )

    # MERGE HTF INTO 1H
    df_1h['htf_bullish'] = (
        df_4h['htf_bullish']
        .reindex(df_1h.index, method='ffill')
    )

    print(f"Fetched candles: {len(df_1h)}")

    return df_1h
    
df = fetch_data()

df = apply_indicators(df)

df = clean_dataframe(df)

signals = pd.Series(
    "HOLD",
    index=df.index
)

last_trade_index = -12

for i in range(200, len(df)):

    # Cooldown
    if i - last_trade_index < SETTINGS["COOLDOWN_CANDLES"]:
        continue

    temp_df = df.iloc[:i]

    signal_data = generate_signal(temp_df)

    signals.iloc[i] = signal_data['signal']

    if signal_data['signal'] == "BUY":

        last_trade_index = i


entries = (
    signals == 'BUY'
)
sl_stop = (( df['atr'] * SETTINGS["SL_ATR_MULTIPLIER"] ) / df['close'])
tp_stop = ((df['atr'] * 6.0) / df['close'])

pf = vbt.Portfolio.from_signals(

    close=df['close'],

    entries=entries,
    tp_stop=SETTINGS["TP_TARGET"],

    sl_stop=sl_stop,
    sl_trail=True,

    fees=SLIPPAGE,
    slippage=SLIPPAGE,

    init_cash=10_000
)
print(
    pf.stats()
)

pf.plot().show()
