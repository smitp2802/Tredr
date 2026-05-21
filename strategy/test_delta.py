import ccxt

exchange = ccxt.delta({
    "apiKey": "YOUR_KEY",
    "secret": "YOUR_SECRET",
})

print(exchange.fetch_balance())
