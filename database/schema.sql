PRAGMA foreign_keys = ON;

-- 1. FACILITIES
CREATE TABLE IF NOT EXISTS facilities (
    facility_id TEXT PRIMARY KEY,
    facility_name TEXT NOT NULL,
    location TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK(status IN ('ACTIVE', 'INACTIVE', 'MAINTENANCE')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. NETWORK NODES
CREATE TABLE IF NOT EXISTS network_nodes (
    node_id TEXT PRIMARY KEY,
    facility_id TEXT NOT NULL,
    node_name TEXT NOT NULL,
    node_type TEXT NOT NULL
        CHECK(node_type IN ('PUMP', 'TANK', 'VALVE')),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (facility_id)
        REFERENCES facilities(facility_id),

    UNIQUE(facility_id, node_name),
    UNIQUE(node_id, facility_id)
);

-- 3. PUMPS
CREATE TABLE IF NOT EXISTS pumps (
    pump_id TEXT PRIMARY KEY,
    facility_id TEXT NOT NULL,
    node_id TEXT NOT NULL UNIQUE,
    pump_name TEXT NOT NULL,
    nominal_flow REAL NOT NULL CHECK(nominal_flow > 0),
    nominal_pressure REAL NOT NULL CHECK(nominal_pressure >= 0),
    nominal_speed REAL NOT NULL DEFAULT 100,
    status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK(status IN ('ACTIVE', 'INACTIVE', 'MAINTENANCE')),

    FOREIGN KEY (facility_id)
        REFERENCES facilities(facility_id),

    FOREIGN KEY (node_id, facility_id)
        REFERENCES network_nodes(node_id, facility_id)
);

-- 4. TANKS
CREATE TABLE IF NOT EXISTS tanks (
    tank_id TEXT PRIMARY KEY,
    facility_id TEXT NOT NULL,
    node_id TEXT NOT NULL UNIQUE,
    tank_name TEXT NOT NULL,
    capacity_liters REAL NOT NULL CHECK(capacity_liters > 0),
    current_level REAL NOT NULL DEFAULT 0
        CHECK(current_level >= 0),
    status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK(status IN ('ACTIVE', 'INACTIVE', 'MAINTENANCE')),

    FOREIGN KEY (facility_id)
        REFERENCES facilities(facility_id),

    FOREIGN KEY (node_id, facility_id)
        REFERENCES network_nodes(node_id, facility_id)
);

-- 5. VALVES
CREATE TABLE IF NOT EXISTS valves (
    valve_id TEXT PRIMARY KEY,
    facility_id TEXT NOT NULL,
    node_id TEXT NOT NULL UNIQUE,
    valve_name TEXT NOT NULL,
    opening_percentage REAL NOT NULL DEFAULT 100
        CHECK(opening_percentage BETWEEN 0 AND 100),
    valve_state TEXT NOT NULL DEFAULT 'OPEN'
        CHECK(valve_state IN ('OPEN', 'CLOSED', 'PARTIALLY_OPEN')),

    FOREIGN KEY (facility_id)
        REFERENCES facilities(facility_id),

    FOREIGN KEY (node_id, facility_id)
        REFERENCES network_nodes(node_id, facility_id)
);

-- 6. PIPES
CREATE TABLE IF NOT EXISTS pipes (
    pipe_id TEXT PRIMARY KEY,
    facility_id TEXT NOT NULL,
    source_node_id TEXT NOT NULL,
    target_node_id TEXT NOT NULL,
    length_meters REAL NOT NULL CHECK(length_meters > 0),
    diameter_mm REAL NOT NULL CHECK(diameter_mm > 0),
    status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK(status IN ('ACTIVE', 'BLOCKED', 'MAINTENANCE')),

    FOREIGN KEY (facility_id)
        REFERENCES facilities(facility_id),

    FOREIGN KEY (source_node_id, facility_id)
        REFERENCES network_nodes(node_id, facility_id),

    FOREIGN KEY (target_node_id, facility_id)
        REFERENCES network_nodes(node_id, facility_id),

    CHECK(source_node_id <> target_node_id)
);

-- 7. SENSORS
CREATE TABLE IF NOT EXISTS sensors (
    sensor_id TEXT PRIMARY KEY,
    facility_id TEXT NOT NULL,
    sensor_name TEXT NOT NULL,
    sensor_type TEXT NOT NULL
        CHECK(sensor_type IN ('FLOW', 'PRESSURE', 'LEVEL')),
    unit TEXT NOT NULL,
    pump_id TEXT,
    tank_id TEXT,
    valve_id TEXT,
    pipe_id TEXT,
    min_value REAL,
    max_value REAL,
    status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK(status IN ('ACTIVE', 'FAULTY', 'INACTIVE')),

    FOREIGN KEY (facility_id)
        REFERENCES facilities(facility_id),
    FOREIGN KEY (pump_id) REFERENCES pumps(pump_id),
    FOREIGN KEY (tank_id) REFERENCES tanks(tank_id),
    FOREIGN KEY (valve_id) REFERENCES valves(valve_id),
    FOREIGN KEY (pipe_id) REFERENCES pipes(pipe_id),

    CHECK (
        (pump_id IS NOT NULL) +
        (tank_id IS NOT NULL) +
        (valve_id IS NOT NULL) +
        (pipe_id IS NOT NULL) = 1
    ),

    CHECK(min_value IS NULL OR max_value IS NULL
          OR min_value <= max_value)
);

-- 8. TELEMETRY
CREATE TABLE IF NOT EXISTS telemetry (
    telemetry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    reading REAL,
    quality_status TEXT NOT NULL DEFAULT 'GOOD'
        CHECK(quality_status IN ('GOOD', 'SUSPECT', 'BAD', 'MISSING')),

    FOREIGN KEY (sensor_id)
        REFERENCES sensors(sensor_id),

    UNIQUE(sensor_id, timestamp)
);

-- 9. OPERATING MODES
CREATE TABLE IF NOT EXISTS operating_modes (
    mode_id TEXT PRIMARY KEY,
    facility_id TEXT NOT NULL,
    mode_name TEXT NOT NULL,
    description TEXT,
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK(status IN ('ACTIVE', 'INACTIVE')),

    FOREIGN KEY (facility_id)
        REFERENCES facilities(facility_id),

    CHECK(effective_to IS NULL OR effective_to >= effective_from)
);

-- 10. ALARMS
CREATE TABLE IF NOT EXISTS alarms (
    alarm_id TEXT PRIMARY KEY,
    facility_id TEXT NOT NULL,
    sensor_id TEXT,
    alarm_type TEXT NOT NULL,
    severity TEXT NOT NULL
        CHECK(severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    description TEXT NOT NULL,
    detected_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN'
        CHECK(status IN ('OPEN', 'ACKNOWLEDGED', 'RESOLVED')),

    FOREIGN KEY (facility_id)
        REFERENCES facilities(facility_id),
    FOREIGN KEY (sensor_id)
        REFERENCES sensors(sensor_id)
);

-- 11. SIMULATION RUNS
CREATE TABLE IF NOT EXISTS simulation_runs (
    simulation_id TEXT PRIMARY KEY,
    facility_id TEXT NOT NULL,
    simulation_name TEXT NOT NULL,
    configuration_json TEXT NOT NULL,
    assumptions_json TEXT NOT NULL,
    output_json TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK(status IN ('PENDING', 'COMPLETED', 'FAILED')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (facility_id)
        REFERENCES facilities(facility_id)
);

-- 12. SIMULATION INPUTS
CREATE TABLE IF NOT EXISTS simulation_inputs (
    input_id INTEGER PRIMARY KEY AUTOINCREMENT,
    simulation_id TEXT NOT NULL,
    parameter_name TEXT NOT NULL,
    original_value REAL,
    simulated_value REAL,
    unit TEXT,

    FOREIGN KEY (simulation_id)
        REFERENCES simulation_runs(simulation_id)
);

-- 13. EQUIPMENT STATE EVENTS
CREATE TABLE IF NOT EXISTS equipment_state_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_type TEXT NOT NULL
        CHECK(equipment_type IN ('PUMP', 'TANK', 'VALVE', 'PIPE')),
    pump_id TEXT REFERENCES pumps(pump_id),
    tank_id TEXT REFERENCES tanks(tank_id),
    valve_id TEXT REFERENCES valves(valve_id),
    pipe_id TEXT REFERENCES pipes(pipe_id),
    previous_state TEXT,
    new_state TEXT NOT NULL,
    changed_at TEXT NOT NULL,
    reason TEXT,

    CHECK (
        (pump_id IS NOT NULL) +
        (tank_id IS NOT NULL) +
        (valve_id IS NOT NULL) +
        (pipe_id IS NOT NULL) = 1
    )
);

-- 14. GROUND TRUTH
CREATE TABLE IF NOT EXISTS ground_truth (
    truth_id INTEGER PRIMARY KEY AUTOINCREMENT,
    telemetry_id INTEGER,
    sensor_id TEXT,
    issue_type TEXT NOT NULL,
    expected_label TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    description TEXT,

    FOREIGN KEY (telemetry_id)
        REFERENCES telemetry(telemetry_id),
    FOREIGN KEY (sensor_id)
        REFERENCES sensors(sensor_id)
);

-- PERFORMANCE INDEXES
CREATE INDEX IF NOT EXISTS idx_telemetry_sensor_time
ON telemetry(sensor_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_alarms_facility
ON alarms(facility_id, detected_at);

CREATE INDEX IF NOT EXISTS idx_pumps_facility
ON pumps(facility_id);

CREATE INDEX IF NOT EXISTS idx_tanks_facility
ON tanks(facility_id);

CREATE INDEX IF NOT EXISTS idx_truth_scenario
ON ground_truth(scenario_id);