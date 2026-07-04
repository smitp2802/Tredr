"""Unit tests for the risk/position sizing module."""

from strategy.risk import calculate_position_size


def test_zero_balance_returns_zero():
    assert calculate_position_size(0, 100, 0.02, 2.0) == 0


def test_zero_atr_returns_zero():
    assert calculate_position_size(10_000, 0, 0.02, 2.0) == 0


def test_position_size_calculation():
    # risk_amount = 200, stop_distance = 300 -> 0 contracts -> min 1
    assert calculate_position_size(10_000, 150, 0.02, 2.0, min_contracts=1) == 1

    # risk_amount = 200, stop_distance = 100 -> 2 contracts
    assert calculate_position_size(10_000, 50, 0.02, 2.0, min_contracts=1) == 2


def test_max_contracts_cap():
    assert calculate_position_size(1_000_000, 10, 0.02, 2.0, max_contracts=5) == 5
