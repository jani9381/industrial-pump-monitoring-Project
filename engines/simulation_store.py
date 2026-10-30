
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List


DB_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "industrial_monitoring.db"
)


def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def save_simulation(
    facility_id: str,
    simulation_name: str,
    configuration: Dict[str, Any],
    assumptions: Dict[str, Any],
    output: Dict[str, Any],
    inputs: Optional[List[Dict[str, Any]]] = None
) -> str:

    inputs = inputs or []
    current_year = datetime.now().year

    conn = get_connection()

    try:
        # Lock the database for a safe sequential ID allocation.
        conn.execute("BEGIN IMMEDIATE")

        existing_ids = conn.execute(
            """
            SELECT simulation_id
            FROM simulation_runs
            WHERE simulation_id LIKE ?
            """,
            (f"SIM-{current_year}-%",)
        ).fetchall()

        existing_numbers = []

        for row in existing_ids:
            try:
                number = int(row["simulation_id"].split("-")[-1])
                existing_numbers.append(number)
            except (ValueError, IndexError):
                continue

        next_number = max(existing_numbers, default=0) + 1

        simulation_id = (
            f"SIM-{current_year}-{next_number:06d}"
        )

        conn.execute(
            """
            INSERT INTO simulation_runs (
                simulation_id,
                facility_id,
                simulation_name,
                configuration_json,
                assumptions_json,
                output_json,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                simulation_id,
                facility_id,
                simulation_name,
                json.dumps(configuration),
                json.dumps(assumptions),
                json.dumps(output),
                "COMPLETED"
            )
        )

        for item in inputs:
            conn.execute(
                """
                INSERT INTO simulation_inputs (
                    simulation_id,
                    parameter_name,
                    original_value,
                    simulated_value,
                    unit
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    simulation_id,
                    item["parameter_name"],
                    item.get("original_value"),
                    item.get("simulated_value"),
                    item.get("unit")
                )
            )

        conn.commit()
        return simulation_id

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def get_simulation_history(
    facility_id: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:

    if limit < 1:
        raise ValueError("Limit must be greater than zero.")

    conn = get_connection()

    try:
        if facility_id:
            rows = conn.execute(
                """
                SELECT *
                FROM simulation_runs
                WHERE facility_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (facility_id, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT *
                FROM simulation_runs
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,)
            ).fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()


def get_simulation_details(simulation_id: str):

    conn = get_connection()

    try:
        simulation = conn.execute(
            """
            SELECT *
            FROM simulation_runs
            WHERE simulation_id = ?
            """,
            (simulation_id,)
        ).fetchone()

        if simulation is None:
            return None

        result = dict(simulation)

        result["configuration"] = json.loads(
            result.pop("configuration_json")
        )

        result["assumptions"] = json.loads(
            result.pop("assumptions_json")
        )

        output_json = result.pop("output_json")

        result["output"] = (
            json.loads(output_json)
            if output_json
            else None
        )

        input_rows = conn.execute(
            """
            SELECT
                parameter_name,
                original_value,
                simulated_value,
                unit
            FROM simulation_inputs
            WHERE simulation_id = ?
            ORDER BY input_id
            """,
            (simulation_id,)
        ).fetchall()

        result["inputs"] = [
            dict(row) for row in input_rows
        ]

        return result

    finally:
        conn.close()
