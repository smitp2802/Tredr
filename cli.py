"""CLI entry point for Tredr.

Commands:
    live      Run the live trading bot.
    backtest  Run a backtest.
    balance   Check the Delta wallet balance.

Examples:
    venv/bin/python cli.py live BTC/USD:USD
    venv/bin/python cli.py backtest BTC/USD:USD --days 90
    venv/bin/python cli.py balance
"""
import argparse
import sys

from strategy.config import DEFAULT_PAIR
from strategy.execution import fetch_usd_balance, get_exchange


def cmd_live(args):
    from strategy.main import main as live_main
    live_main(args.pair)


def cmd_backtest(args):
    from strategy.backtest import run_backtest
    results, trades, equity = run_backtest(
        pair=args.pair,
        timeframe=args.timeframe,
        days=args.days,
        initial_cash=args.cash,
        output_csv=args.out,
    )
    print("\n========== BACKTEST RESULTS ==========")
    for key, value in results.items():
        print(f"{key}: {value}")
    print("======================================\n")


def cmd_balance(args):
    exchange = get_exchange()
    exchange.load_markets()
    usd = fetch_usd_balance()
    print(f"USD Balance: {usd}")


def main():
    parser = argparse.ArgumentParser(prog="tredr", description="Tredr algo trading bot")
    sub = parser.add_subparsers(dest="command", required=True)

    p_live = sub.add_parser("live", help="Run live trading loop")
    p_live.add_argument("pair", nargs="?", default=DEFAULT_PAIR)
    p_live.set_defaults(func=cmd_live)

    p_bt = sub.add_parser("backtest", help="Run a backtest")
    p_bt.add_argument("pair", nargs="?", default=DEFAULT_PAIR)
    p_bt.add_argument("--timeframe", default="1h")
    p_bt.add_argument("--days", type=int, default=180)
    p_bt.add_argument("--cash", type=float, default=10_000)
    p_bt.add_argument("--out", default="logs/backtest_summary.csv")
    p_bt.set_defaults(func=cmd_backtest)

    p_bal = sub.add_parser("balance", help="Check USD balance")
    p_bal.set_defaults(func=cmd_balance)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
