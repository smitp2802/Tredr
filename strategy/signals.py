"""Signal generation for the Tredr trend-following strategy.

The bot is currently LONG ONLY.  Short logic is kept for future use but is
never selected.
"""

from strategy.regimes import detect_regime


def generate_signal(df, settings=None, htf_df=None, quiet=False):
    """Generate a single signal for the most recent row of *df*.

    Args:
        df: DataFrame with indicator columns produced by apply_indicators().
        settings: Dict of parameters.  Uses strategy.config.get_settings() if None.
        htf_df: Optional higher-timeframe DataFrame with indicators.
        quiet: If True, suppress the score-breakdown printout.

    Returns:
        Dict with signal, regime, scores, price and indicator values.
    """
    if settings is None:
        from strategy.config import get_settings
        settings = get_settings()

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    regime = detect_regime(latest['adx'], settings.get("ADX_THRESHOLD", 20))

    # ── Trend conditions ──
    bullish_trend = latest['ema50'] > latest['ema200']
    higher_tf_trend = _higher_tf_trend(df, htf_df)
    bearish_trend = latest['ema50'] < latest['ema200']

    ema_slope_long = latest['ema50'] > df['ema50'].iloc[-5]
    ema_slope_short = latest['ema50'] < df['ema50'].iloc[-5]

    macro_trend_long = latest['ema200'] > df['ema200'].iloc[-10]
    macro_trend_short = latest['ema200'] < df['ema200'].iloc[-10]

    # ── Pullback + breakout ──
    recent_pullback_long = df['low'].tail(3).min() <= latest['ema20']
    recent_pullback_short = df['high'].tail(3).max() >= latest['ema20']
    pullback_ok = latest['close'] < latest['ema20'] * 1.02

    breakout_long = (
        latest['close'] > previous['ema20']
        and bullish_trend
        and latest['volume'] > latest['volume_ma'] * settings["VOLUME_MULTIPLIER"]
    )
    breakout_short = (
        latest['close'] < previous['low']
        and bearish_trend
        and latest['volume'] > latest['volume_ma'] * settings["VOLUME_MULTIPLIER"]
    )

    # ── Momentum / strength / volatility / candle ──
    momentum_long = latest['rsi'] > 53
    momentum_short = latest['rsi'] < 50
    strength = latest['adx'] > settings["ADX_THRESHOLD"]
    atr_expansion = latest['atr'] > df['atr'].rolling(20).mean().iloc[-1]
    bullish_candle = latest['close'] > latest['open']
    bearish_candle = latest['close'] < latest['open']
    volume_confirm = latest['volume'] > latest['volume_ma'] * settings["VOLUME_MULTIPLIER"]

    # ── Overextension guard ──
    distance_from_ema = abs(latest['close'] - latest['ema20']) / latest['ema20']
    ema_threshold = (latest['atr'] / latest['close']) * settings["ATR_THRESHOLD_MULTIPLIER"]
    not_overextended = distance_from_ema < settings["EMA_DISTANCE_THRESHOLD"]

    # ── Score long ──
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
    if higher_tf_trend:
        score_long += 2
    if volume_confirm:
        score_long += 2
    if not_overextended:
        score_long += 1
    if pullback_ok:
        score_long += 1

    # ── Score short (kept for reference, never acted on) ──
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

    # ── Final signal (LONG ONLY) ──
    signal = "HOLD"

    # Quality gates: mandatory higher-timeframe and macro uptrend for longs.
    # This blocks most long entries during bear markets and greatly reduces drawdown.
    mandatory_htf = settings.get("MANDATORY_HTF_TREND", True)
    mandatory_macro = settings.get("MANDATORY_MACRO_TREND", True)

    long_allowed = True
    if mandatory_htf and not higher_tf_trend:
        long_allowed = False
    if mandatory_macro and not macro_trend_long:
        long_allowed = False

    if regime == "TREND" and long_allowed:
        if score_long >= settings["SCORE_THRESHOLD"]:
            signal = "BUY"

    if not quiet:
        print("\n===== SCORE BREAKDOWN =====")
        print("Bullish Trend (EMA50>EMA200):", bullish_trend)
        print("EMA Slope Long:", ema_slope_long)
        print("Macro Trend Long:", macro_trend_long)
        print("Higher TF Trend:", higher_tf_trend)
        print("Momentum Long (RSI>53):", momentum_long)
        print("Strength (ADX):", strength)
        print("Volume Confirm:", volume_confirm)
        print("Bullish Candle:", bullish_candle)
        print("LONG SCORE:", score_long)
        print("SHORT SCORE:", score_short)
        print("===========================\n")

    return {
        "signal": signal,
        "regime": regime,
        "score_long": score_long,
        "score_short": score_short,
        "price": round(float(latest['close']), 2),
        "rsi": round(float(latest['rsi']), 2),
        "adx": round(float(latest['adx']), 2),
        "atr": round(float(latest['atr']), 2),
        "timestamp": latest.name,
        "tp": round(float(latest['close'] * (1 + (settings.get("TP_TARGET") or 0.06))), 2),
        "sl": round(float(latest['close'] - latest['atr'] * settings["SL_ATR_MULTIPLIER"]), 2),
    }


def _higher_tf_trend(df, htf_df):
    """Return True if the higher-timeframe trend is bullish."""
    if htf_df is not None and not htf_df.empty:
        return htf_df['ema20'].iloc[-1] > htf_df['ema50'].iloc[-1]
    # Fallback: use the same-frame 200 EMA slope as a proxy.
    return df['ema200'].iloc[-1] > df['ema200'].iloc[-10]
