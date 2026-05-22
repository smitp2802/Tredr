# strategy/check_balance.py

import ccxt
import os
from dotenv import load_dotenv

load_dotenv()

exchange = ccxt.delta({
    "apiKey": os.getenv("DELTA_API_KEY"),
    "secret": os.getenv("DELTA_API_SECRET"),
})

exchange.set_sandbox_mode(True)

print("KEY =", os.getenv("DELTA_API_KEY"))
print("URL =", exchange.urls["api"])

try:
    balance = exchange.fetch_balance()
    print(balance)

except Exception as e:
    print(type(e))
    print(e)
