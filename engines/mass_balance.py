
from typing import Dict, Any


def calculate_mass_balance(
    inlet_flow: float,
    outlet_flow: float,
    storage_change: float = 0.0,
    duration_minutes: float = 1.0
) -> Dict[str, Any]:
    """
    Calculate mass balance for an industrial water network.

    All flow values are in liters per minute.
    Storage change is in liters per minute equivalent.

    Positive imbalance means excess input.
    Negative imbalance means excess output.
    """

    values = [inlet_flow, outlet_flow, storage_change, duration_minutes]

    if any(value is None for value in values):
        raise ValueError("Mass balance inputs cannot be None.")

    if duration_minutes <= 0:
        raise ValueError("Duration must be greater than zero.")

    if inlet_flow < 0 or outlet_flow < 0:
        raise ValueError("Flow values cannot be negative.")

    net_flow = inlet_flow - outlet_flow - storage_change

    inlet_volume = inlet_flow * duration_minutes
    outlet_volume = outlet_flow * duration_minutes
    storage_volume_change = storage_change * duration_minutes

    imbalance_volume = net_flow * duration_minutes

    imbalance_percentage = (
        abs(net_flow) / inlet_flow * 100
        if inlet_flow > 0
        else (100.0 if net_flow != 0 else 0.0)
    )

    if abs(net_flow) < 0.001:
        status = "BALANCED"
    elif net_flow > 0:
        status = "INPUT_EXCEEDS_OUTPUT"
    else:
        status = "OUTPUT_EXCEEDS_INPUT"

    return {
        "inlet_flow_lpm": round(inlet_flow, 3),
        "outlet_flow_lpm": round(outlet_flow, 3),
        "storage_change_lpm": round(storage_change, 3),
        "net_imbalance_lpm": round(net_flow, 3),
        "inlet_volume_liters": round(inlet_volume, 3),
        "outlet_volume_liters": round(outlet_volume, 3),
        "storage_change_liters": round(storage_volume_change, 3),
        "imbalance_volume_liters": round(imbalance_volume, 3),
        "imbalance_percentage": round(imbalance_percentage, 2),
        "status": status
    }
