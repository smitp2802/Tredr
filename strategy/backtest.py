"""Self-contained backtest engine for the Tredr strategy.

Does not use vectorbt, so it works even when vectorbt's optional dependencies
are broken.

Usage:
    venv/bin/python -m strategy.backtest BTC/USD:USD --days 180 --out results.csv
    venv/bin/python -m strategy.backtest BTC/USDT:USDT --exchange binance --days 180
"""
import argparse
import csv
import os
import time
from datetime import datetime, timedelta, timezone

import ccxt
import pandas as pd

from strategy.config import DEFAULT_PAIR, DEFAULT_TIMEFRAME, DEFAULT_LOOKBACK, get_settings
from strategy.delta_india import DeltaIndiaExchange, fetch_ohlcv_range as fetch_delta_india_ohlcv_range
from strategy.indicators import apply_indicators
from strategy.signals import generate_signal
from strategy.risk import calculate_position_size
from strategy.utils import clean_dataframe

DELTA_PUBLIC_URL = "https://cdn-ind.testnet.deltaex.org"


def get_public_exchange(exchange_name="delta"):
    """Return a public exchange instance for fetching OHLCV."""
    exchange_name = exchange_name.lower()
    if exchange_name == "delta":
        exchange = ccxt.delta({"enableRateLimit": True})
        exchange.urls["api"] = {"public": DELTA_PUBLIC_URL, "private": DELTA_PUBLIC_URL}
        return exchange
    if exchange_name == "binance":
        return ccxt.binance({"enableRateLimit": True})
    if exchange_name == "delta_india":
        return DeltaIndiaExchange()
    raise ValueError(f"Unsupported exchange: {exchange_name}")


def fetch_ohlcv(exchange, pair, timeframe, since=None, limit=None):
    """Fetch a single chunk of OHLCV and return a clean DataFrame."""
    # Delta India wrapper returns a DataFrame directly.
    if isinstance(exchange, DeltaIndiaExchange):
        end = None
        if since is not None:
            # convert ms -> s
            since_sec = since // 1000
            return exchange.fetch_ohlcv(pair, timeframe=timeframe, since=since_sec, limit=limit)
        return exchange.fetch_ohlcv(pair, timeframe=timeframe, limit=limit)

    kwargs = {"timeframe": timeframe}
    if since is not None:
        kwargs["since"] = since
    if limit is not None:
        kwargs["limit"] = limit

    bars = exchange.fetch_ohlcv(pair, **kwargs)
    df = pd.DataFrame(
        bars,
        columns=["timestamp", "open", "high", "low", "close", "volume"],
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    return df


def fetch_ohlcv_range(exchange, pair, timeframe, start, end, limit=1000, quiet=False):
    """Fetch OHLCV between *start* and *end* by paginating.

    Works best with Binance, which supports deep history.  Delta India caps at
    4000 candles per request; Delta testnet only keeps a few weeks of data.
    """
    # Delta India wrapper has its own range pagination.
    if isinstance(exchange, DeltaIndiaExchange):
        return fetch_delta_india_ohlcv_range(pair, timeframe=timeframe, start=start, end=end)

    # Work with tz-naive timestamps to match DataFrame index format.
    start = pd.Timestamp(start).tz_localize(None)
    end = pd.Timestamp(end).tz_localize(None)

    all_bars = []
    current = start
    page = 0
    while current < end:
        since = int(current.timestamp() * 1000)
        bars = exchange.fetch_ohlcv(pair, timeframe=timeframe, since=since, limit=limit)
        if not bars:
            break
        all_bars.extend(bars)
        current = pd.to_datetime(bars[-1][0], unit="ms")
        page += 1
        if not quiet:
            print(f"  fetched page {page}: {len(bars)} bars up to {current}")
        if len(bars) < limit:
            break
        current = current + timedelta(hours=1)
        time.sleep(exchange.rateLimit / 1000.0)

    if not all_bars:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"]).set_index("timestamp")

    df = pd.DataFrame(all_bars, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    df = df[~df.index.duplicated(keep="last")]
    df = df.sort_index()
    return df


def fetch_backtest_data(pair, timeframe="1h", days=180, exchange_name="binance", quiet=False):
    """Fetch both the primary timeframe and 4h HTF data for a backtest.

    Returns:
        Tuple of (df, htf_df).
    """
    exchange = get_public_exchange(exchange_name)
    end = datetime.now(timezone.utc).replace(tzinfo=None)
    start = end - timedelta(days=days + 20)

    if not quiet:
        print(f"Fetching {pair} {timeframe} data from {exchange_name}...")

    if exchange_name in ("binance", "delta_india"):
        df = fetch_ohlcv_range(exchange, pair, timeframe, start, end, quiet=quiet)
    else:
        df = fetch_ohlcv(exchange, pair, timeframe, limit=5000)
        df = df[df.index >= start]
        df = df[df.index <= end]

    if df.empty:
        raise ValueError("No OHLCV data returned")

    df = apply_indicators(df)
    df = clean_dataframe(df)

    htf_start = end - timedelta(days=days + 80)
    if exchange_name in ("binance", "delta_india"):
        htf_df = fetch_ohlcv_range(exchange, pair, "4h", htf_start, end, quiet=quiet)
    else:
        htf_df = fetch_ohlcv(exchange, pair, "4h", limit=2000)
        htf_df = htf_df[htf_df.index >= htf_start]
        htf_df = htf_df[htf_df.index <= end]

    if not htf_df.empty:
        htf_df = apply_indicators(htf_df)
        htf_df = clean_dataframe(htf_df)

    return df, htf_df


def run_backtest_with_data(
    df,
    htf_df=None,
    pair=DEFAULT_PAIR,
    timeframe=DEFAULT_TIMEFRAME,
    initial_cash=10_000,
    output_csv=None,
    exchange_name="delta",
    quiet=False,
    settings_override=None,
):
    """Run the walk-forward backtest on pre-loaded DataFrames."""
    settings = (settings_override or get_settings(pair)).copy()

    warmup = max(200, DEFAULT_LOOKBACK)
    if len(df) <= warmup:
        raise ValueError(f"Not enough candles ({len(df)}), need > {warmup}")

    cash = float(initial_cash)
    position = 0.0  # number of contracts
    contract_value = settings.get("CONTRACT_VALUE", 1.0)
    entry_price = 0.0
    entry_time = None
    stop_price = 0.0
    tp_price = 0.0
    last_trade_index = -settings["COOLDOWN_CANDLES"] - 1
    cooldown = settings["COOLDOWN_CANDLES"]

    trades = []
    equity_curve = []

    sl_mult = settings["SL_ATR_MULTIPLIER"]
    tp_target = settings.get("TP_TARGET")
    fees = settings["FEES"]
    slippage = settings["SLIPPAGE"]

    def _notional(contracts):
        return contracts * contract_value

    def _equity(price):
        if position <= 0:
            return cash
        return cash + _notional(position) * (price - entry_price)

    for i in range(warmup, len(df)):
        row = df.iloc[i]
        timestamp = df.index[i]

        # Check open position exits first
        if position > 0:
            exit_price = None
            exit_reason = None

            if row["low"] <= stop_price:
                exit_price = min(row["open"], stop_price) * (1 - slippage)
                exit_reason = "SL"
            elif tp_price and row["high"] >= tp_price:
                exit_price = max(row["open"], tp_price) * (1 + slippage)
                exit_reason = "TP"

            if exit_price:
                gross_pnl = (exit_price - entry_price) * _notional(position)
                fee_cost = (entry_price + exit_price) * _notional(position) * fees
                net_pnl = gross_pnl - fee_cost
                cash += net_pnl
                position = 0.0

                trades.append({
                    "entry_time": entry_time,
                    "exit_time": timestamp,
                    "entry_price": round(entry_price, 2),
                    "exit_price": round(exit_price, 2),
                    "pnl": round(net_pnl, 2),
                    "reason": exit_reason,
                })
                if not quiet:
                    print(f"  EXIT {exit_reason} @ {exit_price:.2f}  PnL={net_pnl:.2f}  Cash={cash:.2f}")
                continue

        if i - last_trade_index <= cooldown:
            equity_curve.append({"timestamp": timestamp, "equity": _equity(row["close"])})
            continue

        temp_df = df.iloc[:i]
        signal_data = generate_signal(temp_df, settings=settings, htf_df=htf_df, quiet=quiet)

        if signal_data["signal"] == "BUY" and position <= 0:
            position_size = calculate_position_size(
                balance=cash,
                atr=row["atr"],
                risk_percent=settings["RISK_PER_TRADE"],
                atr_multiplier=sl_mult,
                min_contracts=1,
                contract_value=contract_value,
            )

            fill_price = row["open"] * (1 + slippage)
            position = float(position_size)
            entry_price = fill_price
            entry_time = timestamp
            stop_price = fill_price - row["atr"] * sl_mult
            tp_price = fill_price * (1 + tp_target) if tp_target else None

            last_trade_index = i
            trades.append({
                "entry_time": timestamp,
                "exit_time": None,
                "entry_price": round(fill_price, 2),
                "exit_price": None,
                "pnl": None,
                "reason": "ENTRY",
            })
            if not quiet:
                print(f"  ENTRY LONG @ {fill_price:.2f}  contracts={position}  SL={stop_price:.2f}  Cash={cash:.2f}")

        equity_curve.append({"timestamp": timestamp, "equity": _equity(row["close"])})

    final_price = df["close"].iloc[-1]
    if position > 0:
        gross_pnl = (final_price - entry_price) * _notional(position)
        fee_cost = (entry_price + final_price) * _notional(position) * fees
        net_pnl = gross_pnl - fee_cost
        cash += net_pnl
        trades.append({
            "entry_time": entry_time,
            "exit_time": df.index[-1],
            "entry_price": round(entry_price, 2),
            "exit_price": round(final_price, 2),
            "pnl": round(net_pnl, 2),
            "reason": "FINAL",
        })
        position = 0.0

    closed_trades = [t for t in trades if t["reason"] != "ENTRY"]
    winning_trades = [t for t in closed_trades if t["pnl"] > 0]
    losing_trades = [t for t in closed_trades if t["pnl"] <= 0]

    total_return = (cash - initial_cash) / initial_cash
    total_trades = len(closed_trades)
    win_rate = len(winning_trades) / total_trades if total_trades else 0.0
    avg_win = sum(t["pnl"] for t in winning_trades) / len(winning_trades) if winning_trades else 0.0
    avg_loss = sum(t["pnl"] for t in losing_trades) / len(losing_trades) if losing_trades else 0.0
    gross_profit = sum(t["pnl"] for t in winning_trades)
    gross_loss = sum(t["pnl"] for t in losing_trades)
    profit_factor = abs(gross_profit / gross_loss) if gross_loss else float("inf")

    equity_df = pd.DataFrame(equity_curve).set_index("timestamp")
    rolling_max = equity_df["equity"].cummax()
    drawdown = (equity_df["equity"] - rolling_max) / rolling_max
    max_drawdown = float(drawdown.min())

    results = {
        "pair": pair,
        "timeframe": timeframe,
        "exchange": exchange_name,
        "initial_cash": float(initial_cash),
        "final_cash": round(cash, 2),
        "total_return_pct": round(total_return * 100, 2),
        "total_trades": total_trades,
        "win_rate_pct": round(win_rate * 100, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "profit_factor": round(profit_factor, 2),
        "max_drawdown_pct": round(max_drawdown * 100, 2),
    }

    os.makedirs("logs", exist_ok=True)
    if output_csv:
        with open(output_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results.keys())
            writer.writeheader()
            writer.writerow(results)
        if not quiet:
            print(f"\nSummary saved to {output_csv}")

    if not quiet:
        trades_csv = f"logs/backtest_trades_{pair.replace('/', '_')}_{timeframe}.csv"
        with open(trades_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["entry_time", "exit_time", "entry_price", "exit_price", "pnl", "reason"])
            writer.writeheader()
            writer.writerows(trades)
        print(f"Trades saved to {trades_csv}")

        equity_csv = f"logs/backtest_equity_{pair.replace('/', '_')}_{timeframe}.csv"
        equity_df.to_csv(equity_csv)
        print(f"Equity curve saved to {equity_csv}")

    return results, trades, equity_df


def run_backtest(
    pair=DEFAULT_PAIR,
    timeframe=DEFAULT_TIMEFRAME,
    days=180,
    initial_cash=10_000,
    output_csv=None,
    exchange_name="delta",
    quiet=False,
    settings_override=None,
):
    """Run a walk-forward backtest and return a results dict."""
    if not quiet:
        print(f"Backtesting {pair} on {timeframe} ({days} days, exchange={exchange_name})")

    df, htf_df = fetch_backtest_data(pair, timeframe, days, exchange_name, quiet=quiet)

    return run_backtest_with_data(
        df,
        htf_df=htf_df,
        pair=pair,
        timeframe=timeframe,
        initial_cash=initial_cash,
        output_csv=output_csv,
        exchange_name=exchange_name,
        quiet=quiet,
        settings_override=settings_override,
    )


def main():
    parser = argparse.ArgumentParser(description="Backtest the Tredr strategy")
    parser.add_argument("pair", nargs="?", default=DEFAULT_PAIR, help="Trading pair")
    parser.add_argument("--timeframe", default=DEFAULT_TIMEFRAME, help="Candle timeframe")
    parser.add_argument("--days", type=int, default=180, help="Number of days to backtest")
    parser.add_argument("--cash", type=float, default=10_000, help="Initial cash")
    parser.add_argument("--exchange", default="delta", choices=["delta", "binance", "delta_india"], help="Data exchange")
    parser.add_argument("--out", default="logs/backtest_summary.csv", help="Summary CSV output path")
    args = parser.parse_args()

    results, trades, equity = run_backtest(
        pair=args.pair,
        timeframe=args.timeframe,
        days=args.days,
        initial_cash=args.cash,
        output_csv=args.out,
        exchange_name=args.exchange,
    )

    print("\n========== BACKTEST RESULTS ==========")
    for key, value in results.items():
        print(f"{key}: {value}")
    print("======================================\n")


if __name__ == "__main__":
    main()
