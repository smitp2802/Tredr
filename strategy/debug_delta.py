import os
import ccxt
from dotenv import load_dotenv

load_dotenv()

print("\n========== DELTA TEST ==========")

# 1. ENV
api_key = os.getenv("DELTA_API_KEY")
api_secret = os.getenv("DELTA_API_SECRET")

print("\n[1] ENVIRONMENT")

if api_key:
    print("✅ API KEY FOUND")
    print("KEY:", api_key[:8] + "...")
else:
    print("❌ API KEY MISSING")

if api_secret:
    print("✅ API SECRET FOUND")
else:
    print("❌ API SECRET MISSING")

# 2. EXCHANGE
print("\n[2] CONNECTING")

exchange = ccxt.delta({
    "apiKey": api_key,
    "secret": api_secret,
})

exchange.set_sandbox_mode(True)

exchange.urls["api"] = {
    "public": "https://cdn-ind.testnet.deltaex.org",
    "private": "https://cdn-ind.testnet.deltaex.org",
}

# 3. MARKETS
print("\n[3] LOADING MARKETS")

try:
    markets = exchange.load_markets()
    print("✅ Markets Loaded:", len(markets))
except Exception as e:
    print("❌ Market Load Failed")
    print(e)
    raise

# 4. MARKET SYMBOL
print("\n[4] BTC CONTRACT")

try:
    market = exchange.market("BTC/USD:USD")
    print("✅ Symbol Found")
    print("CCXT Symbol:", market["symbol"])
except Exception as e:
    print("❌ Symbol Missing")
    print(e)

# 5. BALANCE
print("\n[5] BALANCE TEST")

try:
    balance = exchange.fetch_balance()

    usd = balance["total"].get("USD", 0)

    print("✅ Auth Success")
    print("USD Balance:", usd)

except Exception as e:
    print("❌ Authentication Failed")
    print(e)

# 6. TICKER
print("\n[6] TICKER TEST")

try:
    ticker = exchange.fetch_ticker("BTC/USD:USD")

    print("✅ Market Data Working")
    print("Last Price:", ticker["last"])

except Exception as e:
    print("❌ Ticker Failed")
    print(e)

print("\n========== DONE ==========")
