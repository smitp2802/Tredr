"""Parameter optimizer for the Tredr long-only strategy.

Fetches deeper history from Binance futures and grid-searches key parameters to
find configurations that keep drawdown low while still producing a reasonable
return and trade count.

Usage:
    venv/bin/python optimize.py

The top configs are printed and saved to logs/optimization_results.csv.
"""
import csv
import itertools
import os
from datetime import datetime, timedelta, timezone

import pandas as pd

from strategy.backtest import fetch_backtest_data, run_backtest_with_data

PAIR = "BTC/USD:USD"
TIMEFRAME = "1h"
EXCHANGE = "delta_india"
DAYS = 120
INITIAL_CASH = 10_000

# Base settings that do not change during the search.
BASE_SETTINGS = {
    "FEES": 0.0005,
    "SLIPPAGE": 0.001,
    "RISK_PER_TRADE": 0.02,
    "EMA_DISTANCE_THRESHOLD": 0.025,
    "ATR_THRESHOLD_MULTIPLIER": 1.2,
    "MANDATORY_HTF_TREND": False,
    "MANDATORY_MACRO_TREND": False,
    "CONTRACT_VALUE": 0.001,
}

# Parameter grid. Keep this modest so the run finishes in a few minutes.
PARAM_GRID = {
    "SCORE_THRESHOLD": [7, 8, 9],
    "VOLUME_MULTIPLIER": [1.2, 1.5],
    "ADX_THRESHOLD": [20, 25],
    "SL_ATR_MULTIPLIER": [1.5, 2.0, 2.5],
    "TP_TARGET": [0.04, 0.06, 0.08],
    "COOLDOWN_CANDLES": [12, 24],
}


def make_settings(combo):
    settings = BASE_SETTINGS.copy()
    settings.update(combo)
    return settings


def score_run(results):
    """Optimization objective: reward low drawdown and positive return.

    Returns a single numeric score where higher is better.
    """
    dd = abs(results["max_drawdown_pct"])
    ret = results["total_return_pct"]
    trades = results["total_trades"]
    pf = results["profit_factor"]

    # Hard filters: ignore configs with catastrophic drawdown or no trades.
    if dd > 50 or trades < 2 or pf < 0.8:
        return -1e9

    # Prefer: small drawdown, positive return, decent trade count, pf > 1.
    return -dd * 10 + ret * 2 + trades * 0.3 + (pf - 1) * 5


def score_drawdown_only(results):
    """Rank purely by lowest drawdown among configs that actually trade."""
    dd = abs(results["max_drawdown_pct"])
    trades = results["total_trades"]
    if trades < 2:
        return -1e9
    return -dd


def main():
    keys = list(PARAM_GRID.keys())
    values = [PARAM_GRID[k] for k in keys]
    combinations = list(itertools.product(*values))

    print(f"Optimizing {PAIR} over {len(combinations)} parameter combinations...")
    print("Fetching data once, then running backtests.\n")

    df, htf_df = fetch_backtest_data(PAIR, TIMEFRAME, DAYS, EXCHANGE, quiet=True)
    print(f"Fetched {len(df)} {TIMEFRAME} candles and {len(htf_df)} 4h candles.\n")

    results_list = []
    for idx, combo in enumerate(combinations, 1):
        params = dict(zip(keys, combo))
        settings = make_settings(params)

        try:
            results, trades, equity = run_backtest_with_data(
                df,
                htf_df=htf_df,
                pair=PAIR,
                timeframe=TIMEFRAME,
                initial_cash=INITIAL_CASH,
                exchange_name=EXCHANGE,
                quiet=True,
                settings_override=settings,
            )
        except Exception as e:
            print(f"[{idx}/{len(combinations)}] {params} -> ERROR: {e}")
            continue

        record = {**params, **results}
        results_list.append(record)
        print(
            f"[{idx}/{len(combinations)}] "
            f"ret={results['total_return_pct']:.2f}% "
            f"dd={results['max_drawdown_pct']:.2f}% "
            f"trades={results['total_trades']} "
            f"pf={results['profit_factor']:.2f}"
        )

    if not results_list:
        print("No valid backtests completed.")
        return

    df_res = pd.DataFrame(results_list)

    df_res["score"] = df_res.apply(score_run, axis=1)
    df_res["dd_score"] = df_res.apply(score_drawdown_only, axis=1)

    os.makedirs("logs", exist_ok=True)
    out_csv = "logs/optimization_results.csv"
    df_res.to_csv(out_csv, index=False)
    print(f"\nAll results saved to {out_csv}")

    print("\n========== TOP 10 BY BALANCED SCORE (return + low drawdown) ==========")
    for _, row in df_res.sort_values("score", ascending=False).head(10).iterrows():
        print(
            f"thr={row['SCORE_THRESHOLD']} vol={row['VOLUME_MULTIPLIER']} "
            f"adx={row['ADX_THRESHOLD']} sl={row['SL_ATR_MULTIPLIER']} "
            f"tp={row['TP_TARGET']} cd={row['COOLDOWN_CANDLES']} | "
            f"ret={row['total_return_pct']:.2f}% dd={row['max_drawdown_pct']:.2f}% "
            f"trades={row['total_trades']} pf={row['profit_factor']:.2f} "
            f"score={row['score']:.2f}"
        )

    print("\n========== TOP 10 BY LOWEST DRAWDOWN (configs that traded) ==========")
    for _, row in df_res.sort_values("dd_score", ascending=False).head(10).iterrows():
        print(
            f"thr={row['SCORE_THRESHOLD']} vol={row['VOLUME_MULTIPLIER']} "
            f"adx={row['ADX_THRESHOLD']} sl={row['SL_ATR_MULTIPLIER']} "
            f"tp={row['TP_TARGET']} cd={row['COOLDOWN_CANDLES']} | "
            f"ret={row['total_return_pct']:.2f}% dd={row['max_drawdown_pct']:.2f}% "
            f"trades={row['total_trades']} pf={row['profit_factor']:.2f}"
        )

    best_balanced = df_res.sort_values("score", ascending=False).iloc[0]
    best_dd = df_res.sort_values("dd_score", ascending=False).iloc[0]

    print("\nBEST BALANCED CONFIG:")
    for k in keys:
        print(f"  {k}: {best_balanced[k]}")
    print(f"  return: {best_balanced['total_return_pct']:.2f}%")
    print(f"  max drawdown: {best_balanced['max_drawdown_pct']:.2f}%")
    print(f"  trades: {best_balanced['total_trades']}")
    print(f"  profit factor: {best_balanced['profit_factor']:.2f}\n")

    print("LOWEST DRAWDOWN CONFIG:")
    for k in keys:
        print(f"  {k}: {best_dd[k]}")
    print(f"  return: {best_dd['total_return_pct']:.2f}%")
    print(f"  max drawdown: {best_dd['max_drawdown_pct']:.2f}%")
    print(f"  trades: {best_dd['total_trades']}")
    print(f"  profit factor: {best_dd['profit_factor']:.2f}\n")


if __name__ == "__main__":
    main()
