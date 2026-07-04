"""Delta Exchange India API client.

Delta India uses its own REST API (api.india.delta.exchange) which is not the
same as the global ccxt `delta` exchange.  This module provides a thin wrapper
so the backtester and live loop can fetch OHLCV and market data for
USD-denominated pairs (e.g. BTCUSD).
"""
import time
import urllib.request
import urllib.parse
import json
from datetime import datetime, timedelta

import pandas as pd

DELTA_INDIA_API = "https://api.india.delta.exchange"

# Map ccxt-like symbols to Delta India API symbols.
SYMBOL_MAP = {
    "BTC/USD:USD": "BTCUSD",
    "ETH/USD:USD": "ETHUSD",
}


def _to_api_symbol(symbol):
    """Convert a ccxt-like symbol to Delta India API symbol."""
    if symbol in SYMBOL_MAP:
        return SYMBOL_MAP[symbol]
    # Strip ccxt formatting if present.
    return symbol.replace("/", "").replace(":", "")


def _to_ccxt_symbol(api_symbol):
    """Convert a Delta India API symbol back to ccxt-like form.

    Best-effort for perpetual futures: BTCUSD -> BTC/USD:USD.
    """
    for ccxt_sym, api_sym in SYMBOL_MAP.items():
        if api_sym == api_symbol:
            return ccxt_sym
    return api_symbol


def _request(path, params=None):
    """Make a GET request to the Delta India API and return JSON."""
    url = DELTA_INDIA_API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def load_markets():
    """Return a list of Delta India products."""
    data = _request("/v2/products")
    if not data.get("success"):
        raise RuntimeError(f"Delta India products request failed: {data}")
    return data.get("result", [])


def fetch_ohlcv(symbol, timeframe="1h", since=None, limit=None, end=None):
    """Fetch OHLCV candles from Delta India.

    Args:
        symbol: ccxt-like symbol (e.g. "BTC/USD:USD") or API symbol ("BTCUSD").
        timeframe: one of 1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 1d, etc.
        since: Unix timestamp (seconds) for start.
        limit: maximum candles to retrieve.  API caps at 2000 per request.
        end: Unix timestamp (seconds) for end.

    Returns:
        pandas.DataFrame with columns [open, high, low, close, volume]
        indexed by timestamp (tz-naive).
    """
    api_symbol = _to_api_symbol(symbol)

    if end is None:
        end = int(time.time())
    if since is None:
        if limit:
            # Each candle is `timeframe` minutes long; approximate seconds.
            minutes = _timeframe_to_minutes(timeframe)
            since = end - limit * minutes * 60
        else:
            since = end - 30 * 24 * 3600

    params = {
        "resolution": timeframe,
        "symbol": api_symbol,
        "start": since,
        "end": end,
    }
    data = _request("/v2/history/candles", params)
    if not data.get("success"):
        raise RuntimeError(f"Delta India candles request failed: {data}")

    candles = data.get("result", [])
    if not candles:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

    df = pd.DataFrame(candles)
    df = df.rename(columns={"time": "timestamp"})
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
    df = df.set_index("timestamp")
    df = df[["open", "high", "low", "close", "volume"]]
    df = df.sort_index()
    df = df[~df.index.duplicated(keep="last")]
    return df


def fetch_ohlcv_range(symbol, timeframe, start, end):
    """Fetch OHLCV across a date range, paginating if needed.

    The Delta India API returns at most 4000 candles per request.
    """
    api_symbol = _to_api_symbol(symbol)
    minutes = _timeframe_to_minutes(timeframe)
    max_candles = 4000
    max_seconds = max_candles * minutes * 60

    start_ts = int(pd.Timestamp(start).timestamp())
    end_ts = int(pd.Timestamp(end).timestamp())

    all_dfs = []
    current_start = start_ts
    while current_start < end_ts:
        current_end = min(current_start + max_seconds, end_ts)
        df = fetch_ohlcv(
            api_symbol,
            timeframe=timeframe,
            since=current_start,
            end=current_end,
        )
        if df.empty:
            break
        all_dfs.append(df)
        current_start = current_end + 1
        # Rate limit safety.
        time.sleep(0.2)

    if not all_dfs:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

    combined = pd.concat(all_dfs)
    combined = combined[~combined.index.duplicated(keep="last")]
    combined = combined.sort_index()
    return combined


def _timeframe_to_minutes(timeframe):
    """Convert a timeframe string to minutes."""
    mapping = {
        "1m": 1,
        "3m": 3,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "2h": 120,
        "4h": 240,
        "6h": 360,
        "1d": 1440,
        "1w": 10080,
    }
    if timeframe in mapping:
        return mapping[timeframe]
    raise ValueError(f"Unsupported timeframe: {timeframe}")


class DeltaIndiaExchange:
    """Minimal ccxt-like wrapper for Delta India public endpoints."""

    def __init__(self):
        self.rateLimit = 200  # ms between requests

    def load_markets(self):
        return load_markets()

    def fetch_ohlcv(self, symbol, timeframe="1h", since=None, limit=None, params=None):
        end = None
        if params and "end" in params:
            end = params["end"]
        if since and limit:
            # approximate end
            minutes = _timeframe_to_minutes(timeframe)
            end = since + limit * minutes * 60
        df = fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=limit, end=end)
        # ccxt returns list of lists; but our backtest expects DataFrame from
        # fetch_ohlcv helper.  Keep DataFrame here.
        return df

    def market(self, symbol):
        """Return minimal market info for a symbol."""
        api_symbol = _to_api_symbol(symbol)
        for product in load_markets():
            if product.get("symbol") == api_symbol:
                return {
                    "symbol": symbol,
                    "id": api_symbol,
                    "info": product,
                    "limits": {
                        "amount": {"min": float(product.get("contract_value", 1))},
                    },
                }
        raise ValueError(f"Delta India market not found: {symbol}")
