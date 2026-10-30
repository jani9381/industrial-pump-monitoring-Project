import json
import sqlite3
from pathlib import Path

from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, Field

from engines.simulation import simulate_pump_operation
from engines.simulation_store import (
    save_simulation,
    get_simulation_history,
    get_simulation_details
)


# --------------------------------------------------
# FASTAPI APPLICATION
# --------------------------------------------------

app = FastAPI(
    title="Industrial Pump Monitoring API",
    description="Industrial equipment monitoring, anomaly detection and simulation",
    version="1.2.0"
)


# --------------------------------------------------
# DATABASE CONFIGURATION
# --------------------------------------------------

DB_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "industrial_monitoring.db"
)


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# --------------------------------------------------
# REQUEST MODELS
# --------------------------------------------------

class AlarmStatusUpdate(BaseModel):
    status: str


class SimulationRequest(BaseModel):
    facility_id: str
    simulation_name: str = Field(min_length=1, max_length=150)

    pump_nominal_flow_lpm: float = Field(gt=0)
    pump_speed_percent: float = Field(ge=0, le=100)
    valve_opening_percent: float = Field(ge=0, le=100)
    leakage_percent: float = Field(default=0.0, ge=0, le=100)

    tank_initial_level_liters: float = Field(ge=0)
    tank_capacity_liters: float = Field(gt=0)

    duration_minutes: float = Field(default=10.0, gt=0)


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "message": "Industrial Monitoring API is running"
    }


# --------------------------------------------------
# FACILITIES
# --------------------------------------------------

@app.get("/facilities")
def get_facilities():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM facilities"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# --------------------------------------------------
# EQUIPMENT
# --------------------------------------------------

@app.get("/equipment")
def get_equipment():
    conn = get_db()
    try:
        pumps = conn.execute("SELECT * FROM pumps").fetchall()
        tanks = conn.execute("SELECT * FROM tanks").fetchall()
        valves = conn.execute("SELECT * FROM valves").fetchall()
        pipes = conn.execute("SELECT * FROM pipes").fetchall()

        return {
            "pumps": [dict(row) for row in pumps],
            "tanks": [dict(row) for row in tanks],
            "valves": [dict(row) for row in valves],
            "pipes": [dict(row) for row in pipes]
        }
    finally:
        conn.close()


# --------------------------------------------------
# SENSOR TELEMETRY
# --------------------------------------------------

@app.get("/telemetry")
def get_telemetry(
    sensor_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000)
):
    conn = get_db()
    try:
        if sensor_id:
            rows = conn.execute(
                """
                SELECT *
                FROM telemetry
                WHERE sensor_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (sensor_id, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT *
                FROM telemetry
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,)
            ).fetchall()

        return [dict(row) for row in rows]
    finally:
        conn.close()


# --------------------------------------------------
# ALARMS
# --------------------------------------------------

@app.get("/alarms")
def get_alarms(
    severity: str | None = None,
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000)
):
    conn = get_db()
    try:
        query = "SELECT * FROM alarms WHERE 1=1"
        params = []

        if severity:
            query += " AND severity = ?"
            params.append(severity.upper())

        if status:
            query += " AND status = ?"
            params.append(status.upper())

        query += " ORDER BY detected_at DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# --------------------------------------------------
# STATISTICS
# --------------------------------------------------

@app.get("/statistics")
def get_statistics():
    conn = get_db()
    try:
        total_facilities = conn.execute(
            "SELECT COUNT(*) FROM facilities"
        ).fetchone()[0]

        total_pumps = conn.execute(
            "SELECT COUNT(*) FROM pumps"
        ).fetchone()[0]

        total_tanks = conn.execute(
            "SELECT COUNT(*) FROM tanks"
        ).fetchone()[0]

        total_alarms = conn.execute(
            "SELECT COUNT(*) FROM alarms"
        ).fetchone()[0]

        open_alarms = conn.execute(
            """
            SELECT COUNT(*)
            FROM alarms
            WHERE status = 'OPEN'
            """
        ).fetchone()[0]

        return {
            "facilities": total_facilities,
            "pumps": total_pumps,
            "tanks": total_tanks,
            "total_alarms": total_alarms,
            "open_alarms": open_alarms
        }
    finally:
        conn.close()


# --------------------------------------------------
# SENSORS
# --------------------------------------------------

@app.get("/sensors")
def get_sensors():
    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT
                sensor_id,
                sensor_name,
                sensor_type,
                unit
            FROM sensors
            ORDER BY sensor_type, sensor_id
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# --------------------------------------------------
# ALARM STATUS UPDATE
# --------------------------------------------------

@app.patch("/alarms/{alarm_id}/status")
def update_alarm_status(
    alarm_id: str,
    update: AlarmStatusUpdate
):
    allowed_statuses = ["ACKNOWLEDGED", "RESOLVED"]
    new_status = update.status.upper()

    if new_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid alarm status"
        )

    conn = get_db()
    try:
        alarm = conn.execute(
            """
            SELECT status
            FROM alarms
            WHERE alarm_id = ?
            """,
            (alarm_id,)
        ).fetchone()

        if alarm is None:
            raise HTTPException(
                status_code=404,
                detail="Alarm not found"
            )

        current_status = alarm["status"]

        if new_status == "ACKNOWLEDGED" and current_status != "OPEN":
            raise HTTPException(
                status_code=400,
                detail="Only OPEN alarms can be acknowledged"
            )

        if new_status == "RESOLVED" and current_status != "ACKNOWLEDGED":
            raise HTTPException(
                status_code=400,
                detail="Only ACKNOWLEDGED alarms can be resolved"
            )

        conn.execute(
            """
            UPDATE alarms
            SET status = ?
            WHERE alarm_id = ?
            """,
            (new_status, alarm_id)
        )
        conn.commit()

        return {
            "message": "Alarm status updated successfully",
            "alarm_id": alarm_id,
            "previous_status": current_status,
            "new_status": new_status
        }
    finally:
        conn.close()


# --------------------------------------------------
# CREATE AND SAVE SIMULATION
# --------------------------------------------------

@app.post("/simulations")
def create_simulation(request: SimulationRequest):

    # Verify facility exists.
    conn = get_db()
    try:
        facility = conn.execute(
            """
            SELECT facility_id
            FROM facilities
            WHERE facility_id = ?
            """,
            (request.facility_id,)
        ).fetchone()
    finally:
        conn.close()

    if facility is None:
        raise HTTPException(
            status_code=404,
            detail="Facility not found"
        )

    if request.tank_initial_level_liters > request.tank_capacity_liters:
        raise HTTPException(
            status_code=400,
            detail="Initial tank level cannot exceed tank capacity"
        )

    # Run simulation, including optional pipeline leakage.
    try:
        output = simulate_pump_operation(
            pump_nominal_flow_lpm=request.pump_nominal_flow_lpm,
            pump_speed_percent=request.pump_speed_percent,
            valve_opening_percent=request.valve_opening_percent,
            tank_initial_level_liters=request.tank_initial_level_liters,
            tank_capacity_liters=request.tank_capacity_liters,
            duration_minutes=request.duration_minutes,
            leakage_percent=request.leakage_percent
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    configuration = {
        "pump_nominal_flow_lpm": request.pump_nominal_flow_lpm,
        "pump_speed_percent": request.pump_speed_percent,
        "valve_opening_percent": request.valve_opening_percent,
        "leakage_percent": request.leakage_percent,
        "tank_initial_level_liters": request.tank_initial_level_liters,
        "tank_capacity_liters": request.tank_capacity_liters,
        "duration_minutes": request.duration_minutes
    }

    assumptions = {
        "flow_model": "Pump flow is proportional to pump speed",
        "leakage_model": "Pipeline leakage is a percentage of pump flow",
        "valve_model": "Delivered flow is proportional to flow remaining after leakage and valve opening",
        "storage_model": "Flow remaining after leakage and valve delivery accumulates in the tank",
        "mass_balance_model": "Pump inflow equals delivered flow plus leakage plus storage change",
        "hydraulic_model": "Simplified linear simulation; not a hydraulic network solver"
    }

    inputs = [
        {
            "parameter_name": "pump_speed",
            "original_value": 100,
            "simulated_value": request.pump_speed_percent,
            "unit": "%"
        },
        {
            "parameter_name": "valve_opening",
            "original_value": 100,
            "simulated_value": request.valve_opening_percent,
            "unit": "%"
        },
        {
            "parameter_name": "pipeline_leakage",
            "original_value": 0,
            "simulated_value": request.leakage_percent,
            "unit": "%"
        },
        {
            "parameter_name": "tank_initial_level",
            "original_value": request.tank_initial_level_liters,
            "simulated_value": request.tank_initial_level_liters,
            "unit": "liters"
        }
    ]

    try:
        simulation_id = save_simulation(
            facility_id=request.facility_id,
            simulation_name=request.simulation_name,
            configuration=configuration,
            assumptions=assumptions,
            output=output,
            inputs=inputs
        )
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=400,
            detail=f"Could not save simulation: {error}"
        )

    return {
        "message": "Simulation completed and saved successfully",
        "simulation_id": simulation_id,
        "facility_id": request.facility_id,
        "status": "COMPLETED",
        "results": output
    }


# --------------------------------------------------
# SIMULATION HISTORY
# --------------------------------------------------

@app.get("/simulations")
def list_simulations(
    facility_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=500)
):
    return get_simulation_history(
        facility_id=facility_id,
        limit=limit
    )


# --------------------------------------------------
# SIMULATION DETAILS
# --------------------------------------------------

@app.get("/simulations/{simulation_id}")
def simulation_details(simulation_id: str):

    result = get_simulation_details(simulation_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Simulation not found"
        )

    return result
