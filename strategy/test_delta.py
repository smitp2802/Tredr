# strategy/test_delta.py

import os
import requests
import time
import hmac
import hashlib
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("DELTA_API_KEY")
api_secret = os.getenv("DELTA_API_SECRET")

path = "/v2/wallet/balances"
method = "GET"
timestamp = str(int(time.time()))

message = method + timestamp + path

signature = hmac.new(
    api_secret.encode(),
    message.encode(),
    hashlib.sha256
).hexdigest()

headers = {
    "api-key": api_key,
    "timestamp": timestamp,
    "signature": signature,
}

url = "https://cdn-ind.testnet.deltaex.org/v2/wallet/balances"

r = requests.get(url, headers=headers)

print("STATUS:", r.status_code)
print(r.text)
