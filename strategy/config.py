import sys

PAIR = "BTCUSDT"
TIMEFRAME = "1h"
LOOKBACK = 500
LIVE_TRADING = False
if not LIVE_TRADING:
    print("LIVE TRADING DISABLED")
return
    
PAIR_CONFIGS = {

    "BTCUSDT": {
        "SCORE_THRESHOLD": 9,
        "VOLUME_MULTIPLIER": 1.5,
        "COOLDOWN_CANDLES": 36,
        "TP_TARGET": 0.10,
        "EMA_DISTANCE_THRESHOLD": 0.015,
        "ATR_THRESHOLD_MULTIPLIER": 1.2,
        "SL_ATR_MULTIPLIER": 2.0,
        "FEES": 0.0005,
        "SLIPPAGE": 0.001,
        "ADX_THRESHOLD": 25
    },

    "ETHUSDT": {
        "SCORE_THRESHOLD": 7,
        "VOLUME_MULTIPLIER": 1.8,
        "COOLDOWN_CANDLES": 48,
        "TP_TARGET": None,
        "EMA_DISTANCE_THRESHOLD": 0.01,
        "ATR_THRESHOLD_MULTIPLIER": 1.2,
        "SL_ATR_MULTIPLIER": 2.0,
        "FEES": 0.0005,
        "SLIPPAGE": 0.001,
        "ADX_THRESHOLD":30
    }

}

PAIR = sys.argv[1]

if PAIR not in PAIR_CONFIGS:
    raise ValueError(f"No config found for {PAIR}")

SETTINGS = PAIR_CONFIGS[PAIR]
