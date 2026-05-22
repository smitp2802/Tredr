from dotenv import load_dotenv
import requests
import os

load_dotenv()

print("KEY =", os.getenv("DELTA_API_KEY"))

r = requests.get(
    "https://testnet-api.delta.exchange/v2/products"
)

print("STATUS =", r.status_code)
print("RESPONSE =", r.text[:200])
