Project: Tredr

Overview:
- Python algo-trading bot for Delta Exchange India Testnet.
- Long-only trend strategy with score-based entries.
- Self-contained backtest engine (no vectorbt dependency).

Exchange:
- ccxt.delta
- API endpoint overridden to: https://cdn-ind.testnet.deltaex.org

Commands:
  venv/bin/python cli.py live BTC/USD:USD
  venv/bin/python cli.py backtest BTC/USD:USD --days 90
  venv/bin/python cli.py balance
  venv/bin/python strategy/diagnostic.py

Files:
- cli.py           CLI entry point
- strategy/main.py Live trading loop
- strategy/backtest.py  Backtest engine
- strategy/signals.py   Signal generation
- strategy/execution.py Order execution
- strategy/indicators.py  TA indicators
- strategy/config.py    Configuration
- strategy/regimes.py   Regime detection
- strategy/journal.py   Trade logging
- strategy/utils.py     Data cleaning
- strategy/risk.py      Position sizing
- strategy/diagnostic.py  Connectivity check

Current Strategy:
- Score-based trend strategy (long only).
- Entry when score_long >= SCORE_THRESHOLD inside a TREND regime.
- EMA trend, momentum, volume, pullback and higher-timeframe filters.
- ATR-based stop loss and optional take profit.
- Optional quality gates: MANDATORY_HTF_TREND and MANDATORY_MACRO_TREND block
  long entries when the higher-timeframe or macro trend is not bullish.
- Position sizing now respects contract value (e.g. 0.001 BTC for Delta India
  BTCUSD) so backtests reflect real notional exposure.

Status:
- Module imports are side-effect free (exchange is created lazily).
- Backtest can run without API keys using public OHLCV data.
- Added Delta India data source (`--exchange delta_india`) using
  `api.india.delta.exchange` with proper USD-denominated pairs (BTC/USD:USD).
- Execution layer now defaults to Delta Exchange India mainnet;
  set `DELTA_USE_TESTNET=true` in `.env` to use testnet.
- Added optimize.py to grid-search parameters and compare drawdown vs return.
- LIVE_TRADING defaults to False; set True in strategy/config.py only when ready.

Optimization Findings (BTC/USD:USD, 1h, ~120 days of Delta India data):
- Default config now tuned for lowest drawdown:
  SCORE_THRESHOLD=9, ADX_THRESHOLD=25, SL_ATR_MULTIPLIER=2.5,
  TP_TARGET=0.04, COOLDOWN_CANDLES=24, CONTRACT_VALUE=0.001.
- Result: max_drawdown -12.98%, total_return -6.06%, 30 trades.
- This reduces the original -27.97% drawdown by more than half.
- Enabling MANDATORY_HTF_TREND + MANDATORY_MACRO_TREND drops drawdown to 0%
  by taking zero trades in the recent bearish/choppy regime.

Next Steps:
- Decide whether to prefer the low-drawdown trading config (default) or the
  zero-trade safety config (enable mandatory trend gates).
- Consider adding short-side signals for direction-neutral performance.
- Verify live connectivity and balance on Delta India before enabling
  LIVE_TRADING.
