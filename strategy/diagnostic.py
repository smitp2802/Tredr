"""Diagnostic script: verify Delta Exchange India connectivity and credentials."""
import os
import sys

from dotenv import load_dotenv

# Allow running directly as `python strategy/diagnostic.py`.
if __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategy.execution import get_exchange

load_dotenv()


def main():
    print("\n========== DELTA DIAGNOSTIC ==========")

    api_key = os.environ.get("DELTA_API_KEY", "")
    api_secret = os.environ.get("DELTA_API_SECRET", "")

    print("\n[1] ENVIRONMENT")
    print("API KEY:", "FOUND" if api_key else "MISSING")
    print("API SECRET:", "FOUND" if api_secret else "MISSING")

    print("\n[2] CONNECTING")
    exchange = get_exchange()

    print("\n[3] LOADING MARKETS")
    try:
        markets = exchange.load_markets()
        print("Markets loaded:", len(markets))
    except Exception as e:
        print("Market load failed:", e)
        return

    print("\n[4] FETCHING BALANCE")
    try:
        balance = exchange.fetch_balance()
        print("USD Balance:", balance["total"].get("USD", 0))
    except Exception as e:
        print("Balance fetch failed:", e)

    print("\n[5] FETCHING BTC/USD:USD OHLCV")
    try:
        ohlcv = exchange.fetch_ohlcv("BTC/USD:USD", timeframe="1h", limit=3)
        print("Latest candle:", ohlcv[-1])
    except Exception as e:
        print("OHLCV fetch failed:", e)

    print("\n========== DONE ==========\n")


if __name__ == "__main__":
    main()
