"""Order execution layer for Delta Exchange India.

The exchange object is created lazily so importing this module does not make
network calls.  This keeps tests and backtests fast and offline-safe.
"""
import os
import ccxt
from dotenv import load_dotenv

from strategy.risk import calculate_position_size
from strategy.config import LIVE_TRADING, get_settings

load_dotenv()

DELTA_API_URLS = {
    "public": "https://api.india.delta.exchange",
    "private": "https://api.india.delta.exchange",
}

# Set DELTA_USE_TESTNET=true in .env to use the India testnet instead.
USE_TESTNET = os.environ.get("DELTA_USE_TESTNET", "").lower() in ("1", "true", "yes")
if USE_TESTNET:
    DELTA_API_URLS = {
        "public": "https://cdn-ind.testnet.deltaex.org",
        "private": "https://cdn-ind.testnet.deltaex.org",
    }

_EXCHANGE = None


def get_exchange():
    """Return a configured ccxt.delta exchange instance."""
    global _EXCHANGE
    if _EXCHANGE is None:
        _EXCHANGE = ccxt.delta({
            "apiKey": os.environ.get("DELTA_API_KEY", ""),
            "secret": os.environ.get("DELTA_API_SECRET", ""),
            "enableRateLimit": True,
        })
        _EXCHANGE.urls["api"] = DELTA_API_URLS
    return _EXCHANGE


def get_public_exchange():
    """Return a public-only exchange instance (no credentials required)."""
    exchange = ccxt.delta({"enableRateLimit": True})
    exchange.urls["api"] = DELTA_API_URLS
    return exchange


def reset_exchange():
    """Reset the cached exchange instance (useful in tests)."""
    global _EXCHANGE
    _EXCHANGE = None


def fetch_usd_balance():
    """Fetch USD balance from the exchange."""
    exchange = get_exchange()
    balance = exchange.fetch_balance()
    return balance["total"].get("USD", 0)


def place_order(signal_data, pair, settings=None):
    """Place a market order for *pair* according to *signal_data*.

    If LIVE_TRADING is False, the order is only printed and logged.
    """
    if settings is None:
        settings = get_settings(pair)

    exchange = get_exchange()
    market = exchange.market(pair)

    usd_balance = fetch_usd_balance()
    atr = signal_data["atr"]
    contract_value = settings.get("CONTRACT_VALUE", 1.0)

    contracts = calculate_position_size(
        balance=usd_balance,
        atr=atr,
        risk_percent=settings["RISK_PER_TRADE"],
        atr_multiplier=settings["SL_ATR_MULTIPLIER"],
        min_contracts=market.get("limits", {}).get("amount", {}).get("min", 1),
        contract_value=contract_value,
    )

    print("\n===== POSITION SIZE =====")
    print("Balance:", usd_balance)
    print("ATR:", atr)
    print("Risk:", settings["RISK_PER_TRADE"] * 100, "%")
    print("Contracts:", contracts)
    print("=========================\n")

    print(f"LIVE_TRADING = {LIVE_TRADING}")
    signal = signal_data["signal"]
    print(f"SIGNAL RECEIVED: {signal}")

    if not LIVE_TRADING:
        print("LIVE TRADING DISABLED -- skipping order")
        _write_trade_log(signal_data, pair)
        return {"status": "paper", "signal": signal, "contracts": contracts}

    try:
        if signal == "BUY":
            print("SENDING BUY ORDER TO DELTA")
            order = exchange.create_market_buy_order(pair, contracts)
        elif signal == "SELL":
            print("SENDING SELL ORDER TO DELTA (closing long)")
            order = exchange.create_market_sell_order(pair, contracts)
        else:
            print(f"Unknown signal {signal!r}, no order sent")
            return {"status": "ignored", "signal": signal}

        print("ORDER SUCCESS")
        print(order)
        _write_trade_log(signal_data, pair)
        return {"status": "filled", "order": order}

    except Exception as e:
        print("ORDER FAILED")
        print(e)
        return {"status": "error", "error": str(e)}


def _write_trade_log(signal_data, pair):
    """Append a human-readable line to trade_log.txt."""
    with open("trade_log.txt", "a") as f:
        f.write(
            f"{signal_data['timestamp']} | "
            f"{pair} | "
            f"{signal_data['signal']} | "
            f"{signal_data['price']} | "
            f"score={signal_data['score_long']} | "
            f"rsi={signal_data['rsi']} | "
            f"adx={signal_data['adx']}\n"
        )
