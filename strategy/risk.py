"""Position sizing and risk helpers."""


def calculate_position_size(
    balance,
    atr,
    risk_percent,
    atr_multiplier,
    min_contracts=1,
    max_contracts=None,
    contract_value=1.0,
):
    """Return the number of contracts to trade.

    Sizing is based on risking *risk_percent* of *balance* with a stop
    placed *atr * atr_multiplier* away from entry.

    Args:
        contract_value: notional size of one contract in units of the
            underlying (e.g. 0.001 BTC for Delta India BTCUSD).
    """
    if balance <= 0:
        return 0
    if atr <= 0 or contract_value <= 0:
        return 0

    risk_amount = balance * risk_percent
    stop_distance = atr * atr_multiplier
    risk_per_contract = stop_distance * contract_value
    contracts = int(risk_amount / risk_per_contract)

    if contracts < min_contracts:
        return min_contracts
    if max_contracts is not None and contracts > max_contracts:
        return max_contracts
    return contracts
