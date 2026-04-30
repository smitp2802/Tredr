import pandas as pd
from indicators import calculate_rsi, calculate_macd, calculate_ema, calculate_bollinger_bands


def generate_signal(df: pd.DataFrame, pair: str) -> dict:
    """
    Generate a trading signal based on RSI + MACD strategy.

    Rules:
      BUY  → RSI < 35 AND MACD line crosses above signal line AND price above EMA50
      SELL → RSI > 65 AND MACD line crosses below signal line AND price below EMA50
      HOLD → everything else
    """
    closes = df["close"]

    # --- Indicators ---
    rsi = calculate_rsi(closes, period=14)
    macd_line, signal_line, histogram = calculate_macd(closes)
    ema50 = calculate_ema(closes, period=50)
    ema200 = calculate_ema(closes, period=200)
    bb_upper, bb_mid, bb_lower = calculate_bollinger_bands(closes)

    # Latest values
    latest_rsi        = round(rsi.iloc[-1], 2)
    latest_macd       = round(macd_line.iloc[-1], 4)
    latest_signal     = round(signal_line.iloc[-1], 4)
    latest_hist       = round(histogram.iloc[-1], 4)
    prev_hist         = round(histogram.iloc[-2], 4)
    latest_price      = round(closes.iloc[-1], 4)
    latest_ema50      = round(ema50.iloc[-1], 4)
    latest_ema200     = round(ema200.iloc[-1], 4)
    latest_bb_upper   = round(bb_upper.iloc[-1], 4)
    latest_bb_lower   = round(bb_lower.iloc[-1], 4)

    # --- MACD crossover detection ---
    macd_bullish_cross = prev_hist < 0 and latest_hist > 0   # crossed above zero
    macd_bearish_cross = prev_hist > 0 and latest_hist < 0   # crossed below zero

    # --- Trend context ---
    uptrend   = latest_price > latest_ema50
    downtrend = latest_price < latest_ema50
    strong_uptrend = latest_ema50 > latest_ema200

    # --- Signal logic ---
    action = "HOLD"
    reasons = []
    confidence = 50  # base confidence

    if latest_rsi < 35 and macd_bullish_cross and uptrend:
        action = "BUY"
        reasons.append(f"RSI oversold at {latest_rsi}")
        reasons.append("MACD bullish crossover")
        reasons.append(f"Price above EMA50 ({latest_ema50})")
        confidence = 70

        # Bonus confidence boosters
        if strong_uptrend:
            reasons.append("EMA50 above EMA200 (strong uptrend)")
            confidence += 10
        if latest_price <= latest_bb_lower:
            reasons.append("Price at lower Bollinger Band (oversold zone)")
            confidence += 10

    elif latest_rsi > 65 and macd_bearish_cross and downtrend:
        action = "SELL"
        reasons.append(f"RSI overbought at {latest_rsi}")
        reasons.append("MACD bearish crossover")
        reasons.append(f"Price below EMA50 ({latest_ema50})")
        confidence = 70

        if not strong_uptrend:
            reasons.append("EMA50 below EMA200 (weak trend)")
            confidence += 10
        if latest_price >= latest_bb_upper:
            reasons.append("Price at upper Bollinger Band (overbought zone)")
            confidence += 10

    else:
        reasons.append("No clear signal — conditions not fully met")
        if latest_rsi < 40:
            reasons.append(f"RSI leaning oversold ({latest_rsi}) but MACD not confirmed")
        elif latest_rsi > 60:
            reasons.append(f"RSI leaning overbought ({latest_rsi}) but MACD not confirmed")

    confidence = min(confidence, 95)  # cap at 95, never 100% confident in markets

    return {
        "pair": pair,
        "action": action,
        "confidence": confidence,
        "price": latest_price,
        "indicators": {
            "rsi": latest_rsi,
            "macd": latest_macd,
            "macd_signal": latest_signal,
            "macd_histogram": latest_hist,
            "ema50": latest_ema50,
            "ema200": latest_ema200,
            "bb_upper": latest_bb_upper,
            "bb_lower": latest_bb_lower,
        },
        "reasons": reasons,
    }
