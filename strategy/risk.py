def calculate_position_size(
    equity,
    risk_percent,
    stop_distance
):

    risk_amount = (
        equity * risk_percent
    )

    size = (
        risk_amount / stop_distance
    )

    return size
