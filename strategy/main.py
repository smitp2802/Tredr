"""
main.py — Trading Rig Entry Point

Fetches 15m OHLCV data from Binance for configured pairs,
runs the RSI + MACD strategy, and fires signals to n8n webhook.

Run continuously:
    python main.py

Or schedule via cron / pm2 for production.
"""

import time
import logging
import requests
import pandas as pd
from datetime import datetime
from trade_signal import generate_signal

# ─── Config ───────────────────────────────────────────────────────────────────

PAIRS = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]   # Add/remove pairs here
INTERVAL = "15m"                              # Binance interval
CANDLE_LIMIT = 250                            # Enough for EMA200 + indicators
LOOP_SLEEP = 60 * 15                          # Re-check every 15 minutes (in seconds)
MIN_CONFIDENCE = 0                          # Only send signal if confidence >= this

N8N_WEBHOOK="http://localhost:5678/webhook-test/trading-signal" # Update with your n8n webhook URL

BINANCE_BASE = "https://api.binance.com/api/v3/klines"

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("../logs/trading.log"),
    ],
)
log = logging.getLogger(__name__)

# ─── Data Fetching ────────────────────────────────────────────────────────────

def fetch_ohlcv(pair: str, interval: str = INTERVAL, limit: int = CANDLE_LIMIT) -> pd.DataFrame:
    """Fetch candlestick data from Binance public API (no API key needed)."""
    params = {"symbol": pair, "interval": interval, "limit": limit}
    response = requests.get(BINANCE_BASE, params=params, timeout=10)
    response.raise_for_status()

    raw = response.json()
    df = pd.DataFrame(raw, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])

    df["close"] = pd.to_numeric(df["close"])
    df["open"]  = pd.to_numeric(df["open"])
    df["high"]  = pd.to_numeric(df["high"])
    df["low"]   = pd.to_numeric(df["low"])
    df["volume"] = pd.to_numeric(df["volume"])
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")

    return df[["open_time", "open", "high", "low", "close", "volume"]]


# ─── Webhook ──────────────────────────────────────────────────────────────────

def send_to_n8n(signal: dict):
    """POST signal payload to n8n webhook."""
    signal["timestamp"] = datetime.utcnow().isoformat()
    try:
        resp = requests.post(N8N_WEBHOOK, json=signal, timeout=10)
        resp.raise_for_status()
        log.info(f"✅ Signal sent to n8n: {signal['pair']} → {signal['action']} (confidence: {signal['confidence']}%)")
    except requests.exceptions.RequestException as e:
        log.error(f"❌ Failed to send signal to n8n: {e}")


# ─── Main Loop ────────────────────────────────────────────────────────────────

def run():
    log.info("🚀 Trading rig started")
    log.info(f"   Pairs: {PAIRS}")
    log.info(f"   Interval: {INTERVAL}")
    log.info(f"   Min confidence to fire: {MIN_CONFIDENCE}%")

    while True:
        log.info("─" * 50)
        log.info(f"🔍 Scanning {len(PAIRS)} pairs...")

        for pair in PAIRS:
            try:
                df = fetch_ohlcv(pair)
                signal = generate_signal(df, pair)

                log.info(
                    f"{pair} | {signal['action']} | RSI: {signal['indicators']['rsi']} "
                    f"| MACD hist: {signal['indicators']['macd_histogram']} "
                    f"| Confidence: {signal['confidence']}%"
                )

                for reason in signal["reasons"]:
                    log.info(f"   → {reason}")

                # Only fire to n8n if signal is actionable and confident enough
                if signal["action"] in ("BUY", "SELL") and signal["confidence"] >= MIN_CONFIDENCE:
                    send_to_n8n(signal)
                else:
                    log.info(f"   ⏸  No action taken (HOLD or low confidence)")

            except Exception as e:
                log.error(f"❌ Error processing {pair}: {e}")

        log.info(f"💤 Sleeping {LOOP_SLEEP // 60} minutes until next scan...")
        time.sleep(LOOP_SLEEP)


if __name__ == "__main__":
    run()
