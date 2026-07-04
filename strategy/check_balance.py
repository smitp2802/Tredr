"""Manual helper: print USD balance from Delta Exchange India."""
from strategy.execution import fetch_usd_balance, get_exchange


if __name__ == "__main__":
    exchange = get_exchange()
    exchange.load_markets()
    print("USD Balance:", fetch_usd_balance())
