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
print("SECRET EXISTS =", os.getenv("DELTA_API_SECRET") is not None)
print(exchange.fetch_balance())
