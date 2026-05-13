import ta


def apply_indicators(df):

    df['ema20'] = ta.trend.ema_indicator(
        df['close'],
        window=20
    )

    df['ema50'] = ta.trend.ema_indicator(
        df['close'],
        window=50
    )

    df['ema200'] = ta.trend.ema_indicator(
        df['close'],
        window=200
    )

    df['rsi'] = ta.momentum.rsi(
        df['close'],
        window=14
    )

    df['adx'] = ta.trend.adx(
        df['high'],
        df['low'],
        df['close'],
        window=14
    )

    df['atr'] = ta.volatility.average_true_range(
        df['high'],
        df['low'],
        df['close'],
        window=14
    )
    df['volume_ma'] = df['volume'].rolling(20).mean()

    return df
