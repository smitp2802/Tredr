def calculate_position_size(
    balance,
    atr,
    risk_percent,
    atr_multiplier
):

    risk_amount = balance * risk_percent

    stop_distance = atr * atr_multiplier

    contracts = max(
        1,
        int(risk_amount / stop_distance)
    )

    return contracts
