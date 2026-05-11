def detect_regime(adx):

    if adx > 25:
        return "TREND"

    return "RANGE"
