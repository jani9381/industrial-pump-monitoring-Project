import sqlite3

import pytest

from engines.simulation import simulate_pump_operation
from engines.mass_balance import calculate_mass_balance
from engines.scenario_validation import is_sensor_fault_mislabeled


def test_pipe_referencing_missing_node_is_rejected():
    """A pipe must reference two existing nodes in its facility."""

    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")

    conn.executescript("""
        CREATE TABLE facilities (
            facility_id TEXT PRIMARY KEY
        );

        CREATE TABLE network_nodes (
            node_id TEXT PRIMARY KEY,
            facility_id TEXT NOT NULL,
            UNIQUE(node_id, facility_id),
            FOREIGN KEY (facility_id)
                REFERENCES facilities(facility_id)
        );

        CREATE TABLE pipes (
            pipe_id TEXT PRIMARY KEY,
            facility_id TEXT NOT NULL,
            source_node_id TEXT NOT NULL,
            target_node_id TEXT NOT NULL,

            FOREIGN KEY (source_node_id, facility_id)
                REFERENCES network_nodes(node_id, facility_id),

            FOREIGN KEY (target_node_id, facility_id)
                REFERENCES network_nodes(node_id, facility_id)
        );

        INSERT INTO facilities VALUES ('FAC-TEST');
        INSERT INTO network_nodes
            VALUES ('NODE-001', 'FAC-TEST');
    """)

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("""
            INSERT INTO pipes
            VALUES ('PIPE-TEST', 'FAC-TEST', 'NODE-001', 'NODE-MISSING')
        """)

    conn.close()


def test_tank_level_exceeding_capacity_is_flagged():
    """Simulation must identify projected tank overflow."""

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
    assert result["tank_final_level_liters"] > result["tank_capacity_liters"]


def test_flow_conservation_violation_is_detected():
    """A significant imbalance must not be reported as balanced."""

    result = calculate_mass_balance(
        inlet_flow=100,
        outlet_flow=80,
        storage_change=0,
        duration_minutes=10
    )

    assert result["status"] != "BALANCED"
    assert result["net_imbalance_lpm"] == 20
    assert result["imbalance_percentage"] == 20
    assert result["imbalance_volume_liters"] == 200


def test_simulation_without_input_configuration_is_rejected():
    """Simulation configuration is mandatory in the database."""

    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")

    conn.executescript("""
        CREATE TABLE facilities (
            facility_id TEXT PRIMARY KEY
        );

        CREATE TABLE simulation_runs (
            simulation_id TEXT PRIMARY KEY,
            facility_id TEXT NOT NULL,
            simulation_name TEXT NOT NULL,
            configuration_json TEXT NOT NULL,
            assumptions_json TEXT NOT NULL,
            output_json TEXT,
            FOREIGN KEY (facility_id)
                REFERENCES facilities(facility_id)
        );

        INSERT INTO facilities VALUES ('FAC-TEST');
    """)

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("""
            INSERT INTO simulation_runs (
                simulation_id,
                facility_id,
                simulation_name,
                configuration_json,
                assumptions_json
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            "SIM-TEST-001",
            "FAC-TEST",
            "Missing configuration test",
            None,
            "{}"
        ))

    conn.close()


def test_sensor_fault_mislabeled_as_process_fault_is_detected():
    """A sensor fault must not receive a process fault label."""

    assert is_sensor_fault_mislabeled(
        issue_type="SENSOR_DRIFT",
        predicted_label="PIPELINE_FLOW_ANOMALY"
    ) is True

    assert is_sensor_fault_mislabeled(
        issue_type="SENSOR_STUCK",
        predicted_label="SENSOR_ANOMALY"
    ) is False
