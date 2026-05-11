"""
backtest.py — Tredr v5 Strategy Backtester

Replicates the full Tredr v5 Pine Script logic in Python using vectorbt.
Fetches historical data from Binance and runs a full statistical backtest.

Usage:
    python backtest.py                          # default BTCUSDT 15m 1 year
    python backtest.py --pair ETHUSDT           # different pair
    python backtest.py --tf 1h --days 500       # different timeframe
    python backtest.py --pair BTCUSDT --tf 4h   # 4hr swing

Requirements:
    pip install vectorbt pandas numpy requests ta
"""

import argparse
import warnings
import requests
import numpy as np
import pandas as pd
import vectorbt as vbt
from datetime import datetime, timedelta, timezone

warnings.filterwarnings("ignore")

# ─── Default Config ───────────────────────────────────────────────

DEFAULT_PAIR    = "BTCUSDT"
DEFAULT_TF      = "15m"
DEFAULT_DAYS    = 365
INITIAL_CAPITAL = 10_000
COMMISSION      = 0.001    # 0.1%
SLIPPAGE        = 0.0005   # 0.05%

RSI_PERIOD      = 14
RSI_OVERSOLD    = 35
RSI_OVERBOUGHT  = 65
MACD_FAST       = 12
MACD_SLOW       = 26
MACD_SIGNAL_LEN = 9
EMA_FAST        = 50
EMA_SLOW        = 200
BB_PERIOD       = 20
BB_STD          = 2.0
ATR_PERIOD      = 14
ADX_PERIOD      = 14
ADX_MIN         = 20
SL_ATR_MULT     = 1.5
RR_RATIO        = 2.0
TP_ATR_MULT     = SL_ATR_MULT * RR_RATIO
SWEEP_LOOKBACK  = 20
OB_LOOKBACK     = 10
MIN_SCORE       = 7

# ─── Data Fetching ────────────────────────────────────────────────

def fetch_binance(pair: str, interval: str, days: int) -> pd.DataFrame:
    print(f"\n📥 Fetching {days} days of {pair} {interval} from Binance...")
    base_url   = "https://api.binance.com/api/v3/klines"
    end_time   = int(datetime.now(timezone.utc).timestamp() * 1000)
    start_time = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1000)
    all_candles= []

    while start_time < end_time:
        params = {"symbol": pair, "interval": interval,
                  "startTime": start_time, "endTime": end_time, "limit": 1000}
        resp    = requests.get(base_url, params=params, timeout=10)
        resp.raise_for_status()
        candles = resp.json()
        if not candles:
            break
        all_candles.extend(candles)
        start_time = candles[-1][0] + 1
        if len(candles) < 1000:
            break

    df = pd.DataFrame(all_candles, columns=[
        "open_time","open","high","low","close","volume",
        "close_time","quote_volume","trades",
        "taker_buy_base","taker_buy_quote","ignore"
    ])
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df.set_index("open_time", inplace=True)
    for col in ["open","high","low","close","volume"]:
        df[col] = pd.to_numeric(df[col])
    df = df[["open","high","low","close","volume"]]
    df = df[~df.index.duplicated(keep="first")].sort_index()
    print(f"   ✅ {len(df)} candles loaded ({df.index[0].date()} → {df.index[-1].date()})")
    return df

# ─── Indicators ───────────────────────────────────────────────────

def calc_rsi(close, period=14):
    delta    = close.diff()
    gain     = delta.clip(lower=0)
    loss     = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period-1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period-1, min_periods=period).mean()
    rs       = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calc_macd(close, fast=12, slow=26, signal=9):
    ema_fast    = close.ewm(span=fast,   adjust=False).mean()
    ema_slow    = close.ewm(span=slow,   adjust=False).mean()
    macd_line   = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram   = macd_line - signal_line
    return macd_line, signal_line, histogram

def calc_atr(high, low, close, period=14):
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs()
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, min_periods=period).mean()

def calc_adx(high, low, close, period=14):
    tr      = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs()
    ], axis=1).max(axis=1)
    dm_plus  = high.diff().clip(lower=0)
    dm_minus = (-low.diff()).clip(lower=0)
    dm_plus  = dm_plus.where(dm_plus > dm_minus, 0)
    dm_minus = dm_minus.where(dm_minus > dm_plus, 0)
    atr      = tr.ewm(alpha=1/period, min_periods=period).mean()
    di_plus  = 100 * dm_plus.ewm(alpha=1/period, min_periods=period).mean() / atr
    di_minus = 100 * dm_minus.ewm(alpha=1/period, min_periods=period).mean() / atr
    dx       = (100 * (di_plus - di_minus).abs() /
                (di_plus + di_minus).replace(0, np.nan))
    return dx.ewm(alpha=1/period, min_periods=period).mean()

def calc_ob_zones(open_, high, low, close, lookback=10):
    body        = (close - open_).abs()
    avg_body    = body.rolling(lookback).mean()
    strong      = body > avg_body * 1.5
    is_bull_ob  = (close > open_) & strong & (close.shift(1) < open_.shift(1))
    is_bear_ob  = (close < open_) & strong & (close.shift(1) > open_.shift(1))
    bull_ob_hi  = open_.shift(1).where(is_bull_ob).ffill()
    bull_ob_lo  = close.shift(1).where(is_bull_ob).ffill()
    bear_ob_hi  = close.shift(1).where(is_bear_ob).ffill()
    bear_ob_lo  = open_.shift(1).where(is_bear_ob).ffill()
    near_bull   = (close >= bull_ob_lo) & (close <= bull_ob_hi)
    near_bear   = (close <= bear_ob_hi) & (close >= bear_ob_lo)
    return near_bull.fillna(False), near_bear.fillna(False)

def calc_fvg(high, low):
    bull_fvg = high.shift(2) < low
    bear_fvg = low.shift(2)  > high
    return bull_fvg.fillna(False), bear_fvg.fillna(False)

def calc_structure(high, low, lookback=10):
    swing_high  = high.rolling(lookback).max().shift(1)
    swing_low   = low.rolling(lookback).min().shift(1)
    bull_bos    = (high > swing_high).replace(False, np.nan).ffill().fillna(False).astype(bool)
    bear_bos    = (low  < swing_low).replace(False, np.nan).ffill().fillna(False).astype(bool)
    return bull_bos, bear_bos

def calc_sweep(high, low, close, open_, lookback=20):
    prev_high   = high.rolling(lookback).max().shift(1)
    prev_low    = low.rolling(lookback).min().shift(1)
    body        = (close - open_).abs()
    bull_wick   = high - pd.concat([open_, close], axis=1).max(axis=1)
    bear_wick   = pd.concat([open_, close], axis=1).min(axis=1) - low
    raw_bull    = (high > prev_high) & (close < prev_high) & (bull_wick >= body * 2)
    raw_bear    = (low  < prev_low)  & (close > prev_low)  & (bear_wick >= body * 2)
    bull_conf   = raw_bull.shift(1) & (close > open_)
    bear_conf   = raw_bear.shift(1) & (close < open_)

    bull_valid  = pd.Series(False, index=high.index)
    bear_valid  = pd.Series(False, index=high.index)
    for i in range(len(high)):
        if bull_conf.iloc[i]:
            bull_valid.iloc[i:min(i+8, len(high))] = True
        if bear_conf.iloc[i]:
            bear_valid.iloc[i:min(i+8, len(high))] = True
    return bull_valid, bear_valid

# ─── Backtest Runner ──────────────────────────────────────────────

def run_backtest(pair, tf, days, min_score):
    df = fetch_binance(pair, tf, days)
    print("\n⚙️  Calculating indicators...")

    o, h, l, c, v = df.open, df.high, df.low, df.close, df.volume

    rsi                      = calc_rsi(c, RSI_PERIOD)
    _, __, hist              = calc_macd(c, MACD_FAST, MACD_SLOW, MACD_SIGNAL_LEN)
    ema50                    = c.ewm(span=EMA_FAST,  adjust=False).mean()
    ema200                   = c.ewm(span=EMA_SLOW,  adjust=False).mean()
    atr                      = calc_atr(h, l, c, ATR_PERIOD)
    atr_avg                  = atr.rolling(50).mean()
    adx                      = calc_adx(h, l, c, ADX_PERIOD)
    near_bull_ob, near_bear_ob = calc_ob_zones(o, h, l, c, OB_LOOKBACK)
    near_bull_fvg, near_bear_fvg = calc_fvg(h, l)
    struct_bull, struct_bear = calc_structure(h, l)
    sweep_bull, sweep_bear   = calc_sweep(h, l, c, o, SWEEP_LOOKBACK)

    macd_bull_cross = (hist > 0) & (hist.shift(1) <= 0)
    macd_bear_cross = (hist < 0) & (hist.shift(1) >= 0)

    vol_ok  = (atr > atr_avg * 0.5) & (atr < atr_avg * 3.0)
    adx_ok  = adx > ADX_MIN

    # Confluence score
    buy_score = (
        (rsi < RSI_OVERSOLD).astype(int)    +
        (hist > 0).astype(int)               +
        (c > ema50).astype(int)              +
        (ema50 > ema200).astype(int)         +
        near_bull_ob.astype(int)             +
        near_bull_fvg.astype(int)            +
        struct_bull.astype(int)              +
        sweep_bull.astype(int)               +
        adx_ok.astype(int)
    )

    sell_score = (
        (rsi > RSI_OVERBOUGHT).astype(int)  +
        (hist < 0).astype(int)               +
        (c < ema50).astype(int)              +
        (ema50 < ema200).astype(int)         +
        near_bear_ob.astype(int)             +
        near_bear_fvg.astype(int)            +
        struct_bear.astype(int)              +
        sweep_bear.astype(int)               +
        adx_ok.astype(int)
    )

    # Entry signals
    entries_long = (
        (rsi < RSI_OVERSOLD) & macd_bull_cross & (c > ema50) &
        near_bull_ob & struct_bull & sweep_bull &
        vol_ok & adx_ok & (buy_score >= min_score)
    )

    entries_short = (
        (rsi > RSI_OVERBOUGHT) & macd_bear_cross & (c < ema50) &
        near_bear_ob & struct_bear & sweep_bear &
        vol_ok & adx_ok & (sell_score >= min_score)
    )

    # Sweep reversals
    sweep_long  = sweep_bull & near_bull_ob & (c > o) & (rsi < 50) & vol_ok
    sweep_short = sweep_bear & near_bear_ob & (c < o) & (rsi > 50) & vol_ok

    all_long  = (entries_long  | sweep_long).fillna(False)
    all_short = (entries_short | sweep_short).fillna(False)

    sl_pct_long  = (atr * SL_ATR_MULT) / c
    tp_pct_long  = (atr * TP_ATR_MULT) / c
    sl_pct_short = (atr * SL_ATR_MULT) / c
    tp_pct_short = (atr * TP_ATR_MULT) / c

    print(f"   Long signals:  {all_long.sum()}")
    print(f"   Short signals: {all_short.sum()}")
    print("\n🔁 Running backtest...")

    pf_long = vbt.Portfolio.from_signals(
        close      = c,
        entries    = all_long,
        exits      = pd.Series(False, index=c.index),
        sl_stop    = sl_pct_long,
        tp_stop    = tp_pct_long,
        init_cash  = INITIAL_CAPITAL / 2,
        fees       = COMMISSION,
        slippage   = SLIPPAGE,
        freq       = tf,
        size       = 0.1,
        size_type  = "percent",
        accumulate = False,
    )

    pf_short = vbt.Portfolio.from_signals(
        close         = c,
        entries       = pd.Series(False, index=c.index),
        exits         = pd.Series(False, index=c.index),
        short_entries = all_short,
        short_exits   = pd.Series(False, index=c.index),
        sl_stop       = sl_pct_short,
        tp_stop       = tp_pct_short,
        init_cash     = INITIAL_CAPITAL / 2,
        fees          = COMMISSION,
        slippage      = SLIPPAGE,
        freq          = tf,
        size          = 0.1,
        size_type     = "percent",
        accumulate    = False,
    )

    return pf_long, pf_short, c

# ─── Results ──────────────────────────────────────────────────────

def print_results(pf_long, pf_short, pair, tf, days):
    sep = "=" * 60

    print(f"\n{sep}")
    print(f"  TREDR v5 — BACKTEST RESULTS")
    print(f"  {pair} | {tf} | Last {days} days")
    print(sep)

    combined_profit = 0

    for label, pf in [("LONG", pf_long), ("SHORT", pf_short)]:
        trades = pf.trades.records_readable
        if len(trades) == 0:
            print(f"\n  {label}: No trades fired")
            continue

        stats        = pf.stats()
        wins         = trades[trades["PnL"] > 0]
        losses       = trades[trades["PnL"] <= 0]
        win_rate     = round(len(wins) / len(trades) * 100, 1)
        gross_profit = wins["PnL"].sum()   if len(wins)   > 0 else 0
        gross_loss   = losses["PnL"].sum() if len(losses) > 0 else 0
        pf_ratio     = round(gross_profit / abs(gross_loss), 2) if gross_loss != 0 else 99
        net          = round(gross_profit + gross_loss, 2)
        combined_profit += net

        print(f"\n  ── {label} ──────────────────────────────────────")
        print(f"  Total Trades  : {len(trades)}")
        print(f"  Win Rate      : {win_rate}%")
        print(f"  Profit Factor : {pf_ratio}")
        print(f"  Net P&L       : ${net}")
        print(f"  Total Return  : {round(stats.get('Total Return [%]', 0), 2)}%")
        print(f"  Max Drawdown  : {round(stats.get('Max Drawdown [%]', 0), 2)}%")
        print(f"  Sharpe Ratio  : {round(stats.get('Sharpe Ratio', 0), 2)}")
        print(f"  Sortino Ratio : {round(stats.get('Sortino Ratio', 0), 2)}")
        print(f"  Avg Win       : ${round(wins['PnL'].mean(), 2) if len(wins) > 0 else 0}")
        print(f"  Avg Loss      : ${round(losses['PnL'].mean(), 2) if len(losses) > 0 else 0}")
        print(f"  Best Trade    : ${round(trades['PnL'].max(), 2)}")
        print(f"  Worst Trade   : ${round(trades['PnL'].min(), 2)}")

        # Save CSV
        fname = f"../logs/backtest_{pair}_{tf}_{label}_{datetime.now().strftime('%Y%m%d')}.csv"
        trades.to_csv(fname, index=False)
        print(f"  Trade log     : {fname}")

    bench = pf_long.stats().get("Benchmark Return [%]", 0)
    print(f"\n  ── SUMMARY ─────────────────────────────────────")
    print(f"  Combined P&L  : ${round(combined_profit, 2)}")
    print(f"  Buy & Hold    : {round(bench, 2)}%")
    print(f"  Strategy vs   : {'✅ Outperformed' if combined_profit > 0 else '❌ Underperformed'}")
    print(sep + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tredr v5 Backtester")
    parser.add_argument("--pair",  default=DEFAULT_PAIR,  help="e.g. BTCUSDT ETHUSDT")
    parser.add_argument("--tf",    default=DEFAULT_TF,    help="15m 1h 4h")
    parser.add_argument("--days",  default=DEFAULT_DAYS,  type=int)
    parser.add_argument("--score", default=MIN_SCORE,     type=int, help="Min confluence score")
    args = parser.parse_args()

    pf_long, pf_short, close = run_backtest(args.pair, args.tf, args.days, args.score)
    print_results(pf_long, pf_short, args.pair, args.tf, args.days)

    print("📊 Opening equity curve...")
    try:
        pf_long.plot().show()
    except Exception:
        print("   (Run in a GUI environment to see the chart)")

    print("✅ Done!\n")
