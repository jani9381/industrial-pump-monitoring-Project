from typing import Dict, Any

from engines.mass_balance import calculate_mass_balance


def simulate_pump_operation(
    pump_nominal_flow_lpm: float,
    pump_speed_percent: float,
    valve_opening_percent: float,
    tank_initial_level_liters: float,
    tank_capacity_liters: float,
    duration_minutes: float = 10.0,
    leakage_percent: float = 0.0
) -> Dict[str, Any]:
    """
    Simulate a simplified pump, valve, pipeline leakage and storage operation.

    Assumptions:
    - Pump flow is proportional to pump speed.
    - Pipeline leakage is a percentage of pump flow.
    - Valve delivery is proportional to the flow remaining after leakage.
    - Flow remaining after leakage and valve delivery accumulates in the tank.
    - Flow is measured in liters per minute.

    This is a simplified linear model, not a hydraulic network solver.
    """

    if pump_nominal_flow_lpm <= 0:
        raise ValueError("Pump nominal flow must be greater than zero.")

    if not 0 <= pump_speed_percent <= 100:
        raise ValueError("Pump speed must be between 0 and 100.")

    if not 0 <= valve_opening_percent <= 100:
        raise ValueError("Valve opening must be between 0 and 100.")

    if not 0 <= leakage_percent <= 100:
        raise ValueError("Leakage percentage must be between 0 and 100.")

    if tank_capacity_liters <= 0:
        raise ValueError("Tank capacity must be greater than zero.")

    if not 0 <= tank_initial_level_liters <= tank_capacity_liters:
        raise ValueError("Initial tank level must be within tank capacity.")

    if duration_minutes <= 0:
        raise ValueError("Duration must be greater than zero.")

    # Calculate pump flow based on operating speed.
    pump_flow = pump_nominal_flow_lpm * pump_speed_percent / 100

    # Calculate pipeline leakage as a share of pump flow.
    leak_flow = pump_flow * leakage_percent / 100

    # Flow available after pipeline leakage.
    available_flow = pump_flow - leak_flow

    # Calculate flow delivered through the valve.
    delivered_flow = available_flow * valve_opening_percent / 100

    # Flow remaining after leakage and delivery accumulates in storage.
    storage_change_rate = available_flow - delivered_flow

    # Calculate tank level after simulation.
    storage_volume_change = storage_change_rate * duration_minutes
    tank_final_level = tank_initial_level_liters + storage_volume_change

    # Check whether the projected tank level exceeds capacity.
    overflow_liters = max(0.0, tank_final_level - tank_capacity_liters)
    tank_capacity_exceeded = overflow_liters > 0

    # Account for both delivered flow and leakage as outflows.
    # pump_flow = delivered_flow + leak_flow + storage_change_rate
    mass_balance = calculate_mass_balance(
        inlet_flow=pump_flow,
        outlet_flow=delivered_flow + leak_flow,
        storage_change=storage_change_rate,
        duration_minutes=duration_minutes
    )

    return {
        "pump_nominal_flow_lpm": round(pump_nominal_flow_lpm, 3),
        "pump_speed_percent": round(pump_speed_percent, 2),
        "valve_opening_percent": round(valve_opening_percent, 2),
        "leakage_percent": round(leakage_percent, 2),
        "pump_flow_lpm": round(pump_flow, 3),
        "leak_flow_lpm": round(leak_flow, 3),
        "flow_available_after_leak_lpm": round(available_flow, 3),
        "delivered_flow_lpm": round(delivered_flow, 3),
        "storage_change_lpm": round(storage_change_rate, 3),
        "duration_minutes": round(duration_minutes, 2),
        "leaked_volume_liters": round(leak_flow * duration_minutes, 3),
        "tank_initial_level_liters": round(tank_initial_level_liters, 3),
        "tank_final_level_liters": round(tank_final_level, 3),
        "tank_capacity_liters": round(tank_capacity_liters, 3),
        "overflow_liters": round(overflow_liters, 3),
        "tank_capacity_exceeded": tank_capacity_exceeded,
        "mass_balance": mass_balance
    }
