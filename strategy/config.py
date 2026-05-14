import sys

PAIR = "BTCUSDT"

PAIR_CONFIGS = {

    "BTCUSDT": {
        "SCORE_THRESHOLD": 9,
        "VOLUME_MULTIPLIER": 1.5,
        "COOLDOWN_CANDLES": 36,
        "TP_TARGET": 0.10,
        "EMA_DISTANCE_THRESHOLD": 0.015,
        "ATR_THRESHOLD_MULTIPLIER": 1.2,
        "SL_ATR_MULTIPLIER": 1.5,
        "FEES": 0.0005,
        "SLIPPAGE": 0.001,
        "ADX_THRESHOLD": 25
    },

    "ETHUSDT": {
        "SCORE_THRESHOLD": 7,
        "VOLUME_MULTIPLIER": 1.3,
        "COOLDOWN_CANDLES": 18,
        "TP_TARGET": 0.08,
        "EMA_DISTANCE_THRESHOLD": 0.02,
        "ATR_THRESHOLD_MULTIPLIER": 1.2,
        "SL_ATR_MULTIPLIER": 1.5,
        "FEES": 0.0005,
        "SLIPPAGE": 0.001,
        "ADX_THRESHOLD":18
    }

}

PAIR = sys.argv[1]

if PAIR not in PAIR_CONFIGS:
    raise ValueError(f"No config found for {PAIR}")

SETTINGS = PAIR_CONFIGS[PAIR]
