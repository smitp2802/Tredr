# Trading Rig 🚀

Crypto algo trading system using RSI + MACD strategy, feeding signals into n8n for AI validation and execution.

## Project Structure

```
Tredr/
├── strategy/
│   ├── main.py          # Main loop — fetches data, generates signals, fires to n8n
│   ├── indicators.py    # RSI, MACD, EMA, Bollinger Bands calculations
│   └── signal.py        # Signal generation logic
├── logs/
│   └── trading.log      # Auto-created on first run
├── requirements.txt
└── README.md
```

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Create logs folder
```bash
mkdir logs
```

### 3. Set up n8n webhook
- Open n8n at http://localhost:5678
- Create a new workflow
- Add a **Webhook** node as the trigger
- Copy the webhook URL and paste it into `main.py` → `N8N_WEBHOOK`

### 4. Configure your pairs
Edit `main.py` and update the `PAIRS` list:
```python
PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
```

### 5. Run
```bash
cd strategy
python main.py
```

---

## How It Works

1. Every 15 minutes, `main.py` fetches the last 250 candles from Binance (free, no API key needed)
2. Calculates RSI, MACD, EMA50, EMA200, Bollinger Bands
3. Applies signal logic:
   - **BUY** → RSI < 35 + MACD bullish crossover + price above EMA50
   - **SELL** → RSI > 65 + MACD bearish crossover + price below EMA50
   - **HOLD** → everything else
4. If confidence ≥ 70%, fires signal JSON to n8n webhook
5. n8n passes it to AI agent for validation, then executes/logs/alerts

---

## Signal Payload (sent to n8n)

```json
{
  "pair": "BTCUSDT",
  "action": "BUY",
  "confidence": 80,
  "price": 67000.0,
  "timestamp": "2025-04-25T10:30:00",
  "indicators": {
    "rsi": 28.4,
    "macd": 120.5,
    "macd_signal": 95.2,
    "macd_histogram": 25.3,
    "ema50": 65800.0,
    "ema200": 62000.0,
    "bb_upper": 70000.0,
    "bb_lower": 63000.0
  },
  "reasons": [
    "RSI oversold at 28.4",
    "MACD bullish crossover",
    "Price above EMA50 (65800.0)",
    "EMA50 above EMA200 (strong uptrend)"
  ]
}
```

---

## n8n Workflow (what to build next)

```
Webhook (receives signal)
  → AI Agent node (Claude/GPT reviews signal + reasons)
  → IF confidence still high
      → HTTP node (execute trade via Binance API)
      → Telegram node (send alert to yourself)
      → Google Sheets node (log the trade)
```

---

## Next Steps

- [ ] Set up n8n webhook and AI agent node
- [ ] Add Binance API key for live trading (testnet first!)
- [ ] Add position sizing logic
- [ ] Add stop-loss / take-profit logic
- [ ] Backtest on historical data using `vectorbt`
- [ ] Expand to NSE stocks (Zerodha Kite API)
- [ ] Expand to Gold/Silver (OANDA API)
