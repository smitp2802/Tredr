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

        recent_pullback_long = (
            df['low'].tail(3).min() <= latest['ema20']
        )

        recent_pullback_short = (
            df['high'].tail(3).max() >= latest['ema20']
        )
        
        breakout_long = (
            latest['close'] > previous['high']
        )
        breakout_short = (
            latest['close'] < previous['low']
        )

        momentum_long = (
            latest['rsi'] > 50
        )

        momentum_short = (
            latest['rsi'] < 48
        )
        atr_expansion = (
            latest['atr'] > df['atr'].rolling(20).mean().iloc[-1]
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
        
        volatility_expansion = (
            latest['atr'] > df['atr'].rolling(20).mean().iloc[-1]
        )
        ema_slope_long = ( 
            latest['ema50'] > df['ema50'].iloc[-5]
        )
        
        if (
            bullish_trend
            and recent_pullback_long
            and breakout_long
            and momentum_long
            and bullish_candle
            and strength
            and volatility_expansion
            and ema_slope_long
            and atr_expansion
        ):
            signal = "BUY"

        elif (
            bearish_trend
            and recent_pullback_short
            and breakout_short
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
