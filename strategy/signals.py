from strategy.regimes import detect_regime
def generate_signal(df):

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    regime = detect_regime(
        latest['adx']
    )

    signal = "HOLD"

    if regime == "TREND":

        bullish_trend = (
            latest['ema50'] > latest['ema200']
        )

        bearish_trend = (
            latest['ema50'] < latest['ema200']
        )

        reclaim_long = (
            latest['close'] > latest['ema20']
            and latest['low'] <= latest['ema20']
        )
        
        reclaim_short = (
            latest['close'] < latest['ema20']
            and latest['high'] >= latest['ema20']
        )

        momentum_long = (
            latest['rsi'] > 50
        )

        momentum_short = (
            latest['rsi'] < 48
        )

        strength = (
            latest['adx'] > 18
        )

        bullish_candle = (
            latest['close'] > latest['open']
        )

        bearish_candle = (
            latest['close'] < latest['open']
        )

        if (
            bullish_trend
            and reclaim_long
            and momentum_long
            and bullish_candle
            and strength
        ):

            signal = "BUY"

        elif (
            bearish_trend
            and reclaim_short
            and momentum_short
            and bearish_candle
            and strength
        ):

            signal = "SELL"

    return {
        "signal": signal,
        "regime": regime,
        "price": round(float(latest['close']), 2),
        "rsi": round(float(latest['rsi']), 2),
        "adx": round(float(latest['adx']), 2)
    }
