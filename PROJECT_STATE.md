Project: Tredr

Current State:
- Python trading bot for Delta Exchange India Testnet
- Exchange: ccxt.delta
- API endpoint overridden to:
  https://cdn-ind.testnet.deltaex.org
- Pair:
  BTC/USD:USD
- Timeframe:
  1h
- Balance:
  $200 demo account
- Indicators:
  EMA20, EMA50, EMA200
  RSI(14)
  ADX(14)
  ATR(14)
  Volume MA(20)

Files:
- main.py
- signals.py
- execution.py
- indicators.py
- config.py
- regimes.py
- journal.py
- utils.py

Current Strategy:
- Score-based trend strategy
- BUY when score_long >= threshold
- Threshold currently 9
- Regime filter using ADX > 25

Current Status:
- Bot connects successfully
- Market data works
- Signal generation works
- Logging works
- Demo trading connection works
- No live trades yet because scores mostly return HOLD

Next Goal:
[whatever we're working on]
