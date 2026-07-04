def detect_regime(adx, threshold=25):
    """Classify market regime based on ADX."""
    if adx > threshold:
        return "TREND"
    return "RANGE"
