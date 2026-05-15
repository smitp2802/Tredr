# Tredr

Algorithmic crypto trading framework for:

* Backtesting
* Paper trading
* Live execution on Delta Exchange
* Multi-pair configuration
* Regime-aware signal generation

---

# Features

## Current Features

* BTC/ETH configurable strategies
* VectorBT backtesting
* Technical indicators
* Regime detection
* Signal scoring system
* Paper trading loop
* Delta Exchange integration
* Logging system
* Pair-specific configs
* Duplicate candle protection
* Risk management scaffolding

---

# Project Structure

```text
Tredr/
│
├── data/
│
├── logs/
│
├── models/
│
├── notebooks/
│
├── strategy/
│   │
│   ├── backtest.py
│   ├── config.py
│   ├── execution.py
│   ├── indicators.py
│   ├── journal.py
│   ├── main.py
│   ├── regimes.py
│   ├── risk.py
│   ├── signals.py
│   └── utils.py
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

---

# File Responsibilities

## `config.py`

Stores:

* pair configs
* timeframe
* fees
* slippage
* thresholds
* live trading toggle

Example:

```python
LIVE_TRADING = False
```

---

## `backtest.py`

Runs historical simulations using:

* CCXT
* Pandas
* VectorBT

Used for:

* strategy optimization
* testing indicators
* evaluating performance

Run:

```bash
python -m strategy.backtest BTCUSDT
```

---

## `main.py`

Main trading engine loop.

Responsibilities:

* fetch candles
* apply indicators
* generate signals
* log trades
* place orders
* avoid duplicate candles

Run:

```bash
python -m strategy.main BTCUSDT
```

---

## `signals.py`

Core signal generation logic.

Handles:

* BUY / SELL / HOLD
* score calculation
* momentum checks
* ADX filtering
* regime filtering

Returns:

```python
{
    "signal": "BUY",
    "score_long": 10,
    "score_short": 3,
    "price": 80413,
    "rsi": 46,
    "adx": 16
}
```

---

## `execution.py`

Handles:

* paper trading
* live execution
* Delta Exchange order placement

Contains:

```python
LIVE_TRADING = False
```

Safety layer before real execution.

---

## `indicators.py`

Computes:

* EMA
* RSI
* ATR
* ADX
* volume metrics
* trend metrics

---

## `regimes.py`

Detects market state.

Examples:

* TREND
* RANGE
* VOLATILE

Used to adapt signal behavior.

---

## `risk.py`

Position sizing and risk management.

Future responsibilities:

* leverage limits
* max drawdown guard
* dynamic sizing
* kill switch

---

## `journal.py`

Trade logging.

Can log:

* timestamp
* pair
* pnl
* regime
* indicators

---

## `utils.py`

Helper functions.

Examples:

* dataframe cleaning
* conversions
* formatting

---

# Installation

## 1. Clone Repository

```bash
git clone https://github.com/smitp2802/Tredr.git

cd Tredr
```

---

## 2. Create Virtual Environment

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Recommended packages:

```text
ccxt
pandas
numpy
vectorbt
python-dotenv
plotly
```

---

# Delta Exchange Setup

## 1. Create API Keys

Go to:

[https://www.delta.exchange/app/account/manageapikeys](https://www.delta.exchange/app/account/manageapikeys)

Enable:

* Trading ✅

Disable:

* Withdrawals ❌

---

## 2. Create `.env`

```env
DELTA_API_KEY=your_api_key
DELTA_API_SECRET=your_api_secret
```

---

## 3. Add `.env` to `.gitignore`

```text
.env
```

---

# Backtesting

## BTC

```bash
python -m strategy.backtest BTCUSDT
```

## ETH

```bash
python -m strategy.backtest ETHUSDT
```

---

# Paper Trading

Keep:

```python
LIVE_TRADING = False
```

Run:

```bash
python -m strategy.main BTCUSDT
```

Expected output:

```text
Waiting for new candle...
```

or:

```text
[PAPER] BUY BTCUSDT
```

---

# Live Trading

⚠️ HIGH RISK

Only enable after extensive paper testing.

In `config.py`:

```python
LIVE_TRADING = True
```

Then run:

```bash
python -m strategy.main BTCUSDT
```

---

# Multi-Pair Configuration

Example:

```python
PAIR_CONFIGS = {
    "BTCUSDT": {
        "SCORE_THRESHOLD": 9,
        "ADX_THRESHOLD": 25
    },

    "ETHUSDT": {
        "SCORE_THRESHOLD": 7,
        "ADX_THRESHOLD": 30
    }
}
```

Run specific pair:

```bash
python -m strategy.main BTCUSDT
```

or:

```bash
python -m strategy.main ETHUSDT
```

---

# Current Trading Flow

```text
Fetch candles
    ↓
Apply indicators
    ↓
Detect regime
    ↓
Generate signal
    ↓
Risk validation
    ↓
Place order
    ↓
Log trade
    ↓
Wait for new candle
```

---

# Recommended Future Improvements

## Infrastructure

* Docker deployment
* VPS hosting
* Redis state tracking
* PostgreSQL logging
* Web dashboard

---

## Trading Logic

* Dynamic TP/SL
* Trailing stop loss
* Portfolio balancing
* Volatility filters
* Funding rate analysis
* Multi-timeframe analysis

---

## AI/ML Ideas

* Reinforcement learning
* Market regime classification
* Sentiment analysis
* Feature engineering
* Transformer-based forecasting

---

# Safety Notes

## NEVER

* hardcode API keys
* enable withdrawals on API
* start with large leverage
* deploy without paper testing

---

## ALWAYS

* use stop losses
* monitor logs
* start with tiny position sizes
* keep backups of configs
* validate exchange quantities

---

# Example Safe Position Sizing

```python
usd_size = 10
quantity = usd_size / price
```

Avoid:

```python
quantity = 1
```

unless intentionally trading full contracts.

---

# Example Runtime

```bash
python -m strategy.main BTCUSDT
```

Output:

```text
Waiting for new candle...

SIGNAL: BUY
PAIR: BTCUSDT
PRICE: 80413
RSI: 46
ADX: 16
```

---

# Philosophy

Tredr is designed as:

```text
research sandbox → paper trader → live execution engine
```

The goal is not just prediction.

The goal is:

* survivability
* consistency
* risk-adjusted execution
* scalable architecture

---

# License

MIT License
