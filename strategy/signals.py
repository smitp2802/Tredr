from strategy.regimes import detect_regime

def generate_signal(df):

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    regime = detect_regime(
        latest['adx']
    )

    signal = "HOLD"

    # ─────────────────────────────
    # Trend Conditions
    # ─────────────────────────────

    bullish_trend = (
        latest['ema50']
        > latest['ema200']
    )

    bearish_trend = (
        latest['ema50']
        < latest['ema200']
    )

    # EMA slope confirmation

    ema_slope_long = (
        latest['ema50']
        > df['ema50'].iloc[-5]
    )

    ema_slope_short = (
        latest['ema50']
        < df['ema50'].iloc[-5]
    )

    # Macro structure confirmation

    macro_trend_long = (
        latest['ema200']
        > df['ema200'].iloc[-10]
    )

    macro_trend_short = (
        latest['ema200']
        < df['ema200'].iloc[-10]
    )

    # ─────────────────────────────
    # Pullback + Breakout
    # ─────────────────────────────

    recent_pullback_long = (
        df['low'].tail(3).min()
        <= latest['ema20']
    )

    recent_pullback_short = (
        df['high'].tail(3).max()
        >= latest['ema20']
    )

    breakout_long = (
        latest['close']
        > previous['ema20']
    )

    breakout_short = (
        latest['close']
        < previous['low']
    )

    # ─────────────────────────────
    # Momentum
    # ─────────────────────────────

    momentum_long = (
        latest['rsi']
        > 50
    )

    momentum_short = (
        latest['rsi']
        < 50
    )

    # ─────────────────────────────
    # Strength
    # ─────────────────────────────

    strength = (
        latest['adx']
        > 18
    )

    # ─────────────────────────────
    # Volatility Expansion
    # ─────────────────────────────

    atr_expansion = (
        latest['atr']
        > df['atr'].rolling(20).mean().iloc[-1]
    )

    # ─────────────────────────────
    # Candle Confirmation
    # ─────────────────────────────

    bullish_candle = (
        latest['close'] > latest['open']
        and
        previous['close'] > previous['open']
    )

    bearish_candle = (
        latest['close']
        < latest['open']
    )

    # ─────────────────────────────
    # LONG SCORE
    # ─────────────────────────────

    score_long = 0

    if bullish_trend:
        score_long += 2

    if ema_slope_long:
        score_long += 1

    if macro_trend_long:
        score_long += 1

    if recent_pullback_long:
        score_long += 1

    if breakout_long:
        score_long += 2

    if momentum_long:
        score_long += 1

    if strength:
        score_long += 1

    if bullish_candle:
        score_long += 1

    # ─────────────────────────────
    # SHORT SCORE
    # ─────────────────────────────

    score_short = 0

    if bearish_trend:
        score_short += 2

    if ema_slope_short:
        score_short += 1

    if macro_trend_short:
        score_short += 1

    if recent_pullback_short:
        score_short += 1

    if breakout_short:
        score_short += 2

    if momentum_short:
        score_short += 1

    if strength:
        score_short += 1

    if atr_expansion:
        score_short += 1

    if bearish_candle:
        score_short += 1

    # ─────────────────────────────
    # Final Signal
    # ─────────────────────────────

    #if regime == "TREND":
    if True:
        # LONG ONLY FOR NOW

        if score_long >= 8:
            signal = "BUY"

        # Uncomment later if needed

        # elif score_short >= 7:
        #     signal = "SELL"

    return {
        "signal": signal,
        "regime": regime,
        "score_long": score_long,
        "score_short": score_short,
        "price": round(float(latest['close']), 2),
        "rsi": round(float(latest['rsi']), 2),
        "adx": round(float(latest['adx']), 2)
    }
