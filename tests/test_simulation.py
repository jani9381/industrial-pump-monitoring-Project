
import pytest

from engines.simulation import simulate_pump_operation


def test_normal_pump_simulation():

    result = simulate_pump_operation(
        pump_nominal_flow_lpm=200,
        pump_speed_percent=80,
        valve_opening_percent=75,
        tank_initial_level_liters=5000,
        tank_capacity_liters=10000,
        duration_minutes=10
    )

    assert result["pump_flow_lpm"] == 160
    assert result["delivered_flow_lpm"] == 120
    assert result["tank_final_level_liters"] == 5400
    assert result["mass_balance"]["status"] == "BALANCED"


def test_closed_valve():

    result = simulate_pump_operation(
        pump_nominal_flow_lpm=200,
        pump_speed_percent=100,
        valve_opening_percent=0,
        tank_initial_level_liters=1000,
        tank_capacity_liters=10000,
        duration_minutes=5
    )

    assert result["pump_flow_lpm"] == 200
    assert result["delivered_flow_lpm"] == 0
    assert result["tank_final_level_liters"] == 2000


def test_fully_open_valve():

    result = simulate_pump_operation(
        pump_nominal_flow_lpm=200,
        pump_speed_percent=100,
        valve_opening_percent=100,
        tank_initial_level_liters=1000,
        tank_capacity_liters=10000,
        duration_minutes=5
    )

    assert result["delivered_flow_lpm"] == 200
    assert result["tank_final_level_liters"] == 1000


def test_tank_overflow_warning():

    result = simulate_pump_operation(
        pump_nominal_flow_lpm=200,
        pump_speed_percent=100,
        valve_opening_percent=50,
        tank_initial_level_liters=9500,
        tank_capacity_liters=10000,
        duration_minutes=10
    )

    assert result["tank_capacity_exceeded"] is True
    assert result["overflow_liters"] == 500


def test_invalid_pump_speed():

    with pytest.raises(ValueError):
        simulate_pump_operation(
            pump_nominal_flow_lpm=200,
            pump_speed_percent=120,
            valve_opening_percent=50,
            tank_initial_level_liters=1000,
            tank_capacity_liters=10000
        )
