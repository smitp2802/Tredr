"""Trading strategy configuration.

This module contains only pure configuration.  It does NOT read sys.argv or
access the filesystem, so it is safe to import from tests, backtests, and the
live bot without side effects.
"""

DEFAULT_PAIR = "BTC/USD:USD"
DEFAULT_TIMEFRAME = "1h"
DEFAULT_LOOKBACK = 500

# Set to False to log signals without sending real orders.
LIVE_TRADING = False


def _base_config(
    score_threshold=9,
    volume_multiplier=1.2,
    cooldown=24,
    tp=0.04,
    ema_distance=0.025,
    sl_atr=2.5,
    adx=25,
    contract_value=0.001,
    mandatory_htf=False,
    mandatory_macro=False,
):
    """Return a base configuration dict with sensible defaults."""
    return {
        "SCORE_THRESHOLD": score_threshold,
        "VOLUME_MULTIPLIER": volume_multiplier,
        "COOLDOWN_CANDLES": cooldown,
        "TP_TARGET": tp,
        "EMA_DISTANCE_THRESHOLD": ema_distance,
        "ATR_THRESHOLD_MULTIPLIER": 1.2,
        "SL_ATR_MULTIPLIER": sl_atr,
        "FEES": 0.0005,
        "SLIPPAGE": 0.001,
        "RISK_PER_TRADE": 0.02,
        "ADX_THRESHOLD": adx,
        "MANDATORY_HTF_TREND": mandatory_htf,
        "MANDATORY_MACRO_TREND": mandatory_macro,
        "CONTRACT_VALUE": contract_value,
    }


PAIR_CONFIGS = {
    # Delta India BTCUSD perpetual.
    # Contract value is 0.001 BTC per contract.
    # Tuned on ~120 days of Delta India 1h data to minimise max drawdown.
    "BTC/USD:USD": _base_config(
        score_threshold=9,
        volume_multiplier=1.2,
        cooldown=24,
        tp=0.04,
        sl_atr=2.5,
        adx=25,
        contract_value=0.001,
        mandatory_htf=False,
        mandatory_macro=False,
    ),
    "ETH/USD:USD": _base_config(
        score_threshold=9,
        volume_multiplier=1.2,
        cooldown=24,
        tp=0.04,
        sl_atr=2.5,
        adx=25,
        contract_value=0.001,
        mandatory_htf=False,
        mandatory_macro=False,
    ),
    # Binance futures proxy (used only for deeper history checks).
    "BTC/USDT:USDT": _base_config(
        score_threshold=9,
        volume_multiplier=1.2,
        cooldown=24,
        tp=0.04,
        sl_atr=2.5,
        adx=25,
        contract_value=1.0,
        mandatory_htf=False,
        mandatory_macro=False,
    ),
}


def get_settings(pair=None):
    """Return the settings dict for the requested pair.

    Falls back to DEFAULT_PAIR when none is given.
    """
    pair = pair or DEFAULT_PAIR
    if pair not in PAIR_CONFIGS:
        raise ValueError(f"No config found for {pair!r}")
    return PAIR_CONFIGS[pair]
