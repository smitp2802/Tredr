# strategy/debug_delta.py

import os
import ccxt
import requests
from dotenv import load_dotenv

load_dotenv()

print("\n===== ENVIRONMENT =====")
print("KEY =", os.getenv("DELTA_API_KEY"))
print("SECRET EXISTS =", bool(os.getenv("DELTA_API_SECRET")))

exchange = ccxt.delta({
    "apiKey": os.getenv("DELTA_API_KEY"),
    "secret": os.getenv("DELTA_API_SECRET"),
})

exchange.set_sandbox_mode(True)

print(exchange.apiKey)
print(len(exchange.secret))

exchange = ccxt.delta({
    "apiKey": os.getenv("DELTA_API_KEY"),
    "secret": os.getenv("DELTA_API_SECRET"),
})

exchange.set_sandbox_mode(True)

# Add this here
exchange.urls["api"] = {
    "public": "https://cdn-ind.testnet.deltaex.org",
    "private": "https://cdn-ind.testnet.deltaex.org",
}

market = exchange.market("BTC/USD:USD")

print(market)
print(exchange.fetch_balance())

#print("\n===== CCXT URLS =====")
#print(exchange.urls["api"])

#print("\n===== KEY LENGTHS =====")
#print("KEY LEN =", len(os.getenv("DELTA_API_KEY")))
#print("SECRET LEN =", len(os.getenv("DELTA_API_SECRET")))

#print("\n===== PUBLIC TEST =====")
#try:
#    markets = exchange.fetch_markets()
#    print("SUCCESS")
#    print("Markets Loaded:", len(markets))
#except Exception as e:
#    print("FAILED")
#     print(type(e))
#    print(e)

#print("\n===== PRIVATE TEST =====")
#try:
#    balance = exchange.fetch_balance()
#    print("SUCCESS")
#    print(balance)
#except Exception as e:
#    print("FAILED")
#    print(type(e))
#    print(e)

#print("\n===== RAW TESTNET CHECK =====")
#try:
#    r = requests.get(
#        "https://testnet-api.delta.exchange/v2/products"
#    )
#    print("STATUS =", r.status_code)
#except Exception as e:
#    print("FAILED")
#    print(e)

#print("\n===== ACCOUNT TEST =====")

#try:
#    response = exchange.privateGetUsersMe()
#    print(response)

#except Exception as e:
#    print(type(e))
#    print(e)

#print("\n===== AVAILABLE PRIVATE METHODS =====")

#for method in dir(exchange):
#    if "private" in method.lower():
#        print(method)
