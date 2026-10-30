
from engines.simulation_store import (
    save_simulation,
    get_simulation_history,
    get_simulation_details
)


def test_save_and_retrieve_simulation():

    simulation_id = save_simulation(
        facility_id="FAC-001",
        simulation_name="Pump Performance Test",

        configuration={
            "pump_speed_percent": 80,
            "valve_opening_percent": 75
        },

        assumptions={
            "flow_model": "Linear pump speed model"
        },

        output={
            "pump_flow_lpm": 160,
            "delivered_flow_lpm": 120
        },

        inputs=[
            {
                "parameter_name": "pump_speed",
                "original_value": 100,
                "simulated_value": 80,
                "unit": "%"
            },
            {
                "parameter_name": "valve_opening",
                "original_value": 100,
                "simulated_value": 75,
                "unit": "%"
            }
        ]
    )

    assert simulation_id.startswith("SIM-")

    details = get_simulation_details(simulation_id)

    assert details is not None
    assert details["status"] == "COMPLETED"
    assert details["facility_id"] == "FAC-001"
    assert len(details["inputs"]) == 2
    assert details["output"]["pump_flow_lpm"] == 160


def test_simulation_history():

    history = get_simulation_history(
        facility_id="FAC-001",
        limit=10
    )

    assert isinstance(history, list)
    assert len(history) > 0


def test_missing_simulation():

    result = get_simulation_details("SIM-DOES-NOT-EXIST")

    assert result is None
