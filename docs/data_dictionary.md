\# Industrial Pump Monitoring System — Data Dictionary



\## 1. Purpose



This document describes the database entities, field types, required and optional attributes, constraints, units, and relationships for the Industrial Pump Monitoring System.



Database: SQLite  

Schema source: `database/schema.sql`  

Data source: Synthetic generated industrial monitoring data.



\## 2. Common conventions



\- Primary keys uniquely identify records.

\- Foreign keys reference parent records.

\- Required fields use `NOT NULL`.

\- Optional fields may contain NULL.

\- Status and category values are restricted using CHECK constraints where defined.

\- Timestamps are stored as TEXT.

\- Flow is measured in liters per minute (L/min).

\- Tank capacity and levels are measured in liters (L).

\- Pipe length is measured in meters (m).

\- Pipe diameter is measured in millimeters (mm).

\- Percentages range from 0 to 100 where specified.



\## 3. Core entities



\### 3.1 facilities



| Field | Type | Required | Validation / allowed values | Unique |

|---|---|---|---|---|

| facility\_id | TEXT | Yes | Facility identifier, e.g. FAC-001 | PK |

| facility\_name | TEXT | Yes | Non-empty facility name | No |

| location | TEXT | No | Facility location | No |

| status | TEXT | Yes | ACTIVE, INACTIVE, MAINTENANCE | No |

| created\_at | TEXT | Yes | Defaults to CURRENT\_TIMESTAMP | No |



\### 3.2 pumps



| Field | Type | Required | Validation / allowed values | Unique |

|---|---|---|---|---|

| pump\_id | TEXT | Yes | Pump identifier | PK |

| facility\_id | TEXT | Yes | Must reference facilities | No |

| node\_id | TEXT | Yes | Must reference a node in the same facility | Yes |

| pump\_name | TEXT | Yes | Non-empty name | No |

| nominal\_flow | REAL | Yes | Greater than 0; L/min | No |

| nominal\_pressure | REAL | Yes | Greater than or equal to 0; pressure unit must be defined by source data | No |

| nominal\_speed | REAL | Yes | Defaults to 100; percentage convention | No |

| status | TEXT | Yes | ACTIVE, INACTIVE, MAINTENANCE | No |



\### 3.3 tanks



| Field | Type | Required | Validation / allowed values | Unique |

|---|---|---|---|---|

| tank\_id | TEXT | Yes | Tank identifier | PK |

| facility\_id | TEXT | Yes | Must reference facilities | No |

| node\_id | TEXT | Yes | Must reference a node in the same facility | Yes |

| tank\_name | TEXT | Yes | Non-empty name | No |

| capacity\_liters | REAL | Yes | Greater than 0; L | No |

| current\_level | REAL | Yes | Greater than or equal to 0; L | No |

| status | TEXT | Yes | ACTIVE, INACTIVE, MAINTENANCE | No |



Note: The current schema does not enforce current\_level <= capacity\_liters at database level. Simulation logic separately detects projected overflow.



\### 3.4 valves



| Field | Type | Required | Validation / allowed values | Unique |

|---|---|---|---|---|

| valve\_id | TEXT | Yes | Valve identifier | PK |

| facility\_id | TEXT | Yes | Must reference facilities | No |

| node\_id | TEXT | Yes | Must reference a node in the same facility | Yes |

| valve\_name | TEXT | Yes | Non-empty name | No |

| opening\_percentage | REAL | Yes | 0–100; percentage | No |

| valve\_state | TEXT | Yes | OPEN, CLOSED, PARTIALLY\_OPEN | No |



\### 3.5 pipes



| Field | Type | Required | Validation / allowed values | Unique |

|---|---|---|---|---|

| pipe\_id | TEXT | Yes | Pipe identifier | PK |

| facility\_id | TEXT | Yes | Must reference facilities | No |

| source\_node\_id | TEXT | Yes | Must reference a node in the same facility | No |

| target\_node\_id | TEXT | Yes | Must reference a node in the same facility | No |

| length\_meters | REAL | Yes | Greater than 0; m | No |

| diameter\_mm | REAL | Yes | Greater than 0; mm | No |

| status | TEXT | Yes | ACTIVE, BLOCKED, MAINTENANCE | No |



Validation: Source and target nodes must be different.



\### 3.6 sensors



| Field | Type | Required | Validation / allowed values | Unique |

|---|---|---|---|---|

| sensor\_id | TEXT | Yes | Sensor identifier | PK |

| facility\_id | TEXT | Yes | Must reference facilities | No |

| sensor\_name | TEXT | Yes | Non-empty name | No |

| sensor\_type | TEXT | Yes | FLOW, PRESSURE, LEVEL | No |

| unit | TEXT | Yes | Measurement unit | No |

| pump\_id | TEXT | No | Must reference pumps if provided | No |

| tank\_id | TEXT | No | Must reference tanks if provided | No |

| valve\_id | TEXT | No | Must reference valves if provided | No |

| pipe\_id | TEXT | No | Must reference pipes if provided | No |

| min\_value | REAL | No | Optional minimum measurement | No |

| max\_value | REAL | No | Optional maximum measurement | No |

| status | TEXT | Yes | ACTIVE, FAULTY, INACTIVE | No |



Validation: Exactly one of pump\_id, tank\_id, valve\_id, or pipe\_id must be populated. If both limits are provided, min\_value must not exceed max\_value.



\### 3.7 telemetry



| Field | Type | Required | Validation / allowed values | Unique |

|---|---|---|---|---|

| telemetry\_id | INTEGER | Generated | AUTOINCREMENT primary key | PK |

| sensor\_id | TEXT | Yes | Must reference sensors | No |

| timestamp | TEXT | Yes | Reading timestamp | Combined |

| reading | REAL | No | Sensor measurement in sensor.unit | No |

| quality\_status | TEXT | Yes | GOOD, SUSPECT, BAD, MISSING | No |



Unique combination: sensor\_id + timestamp.



\### 3.8 operating\_modes



| Field | Type | Required | Validation / allowed values | Unique |

|---|---|---|---|---|

| mode\_id | TEXT | Yes | Operating mode identifier | PK |

| facility\_id | TEXT | Yes | Must reference facilities | No |

| mode\_name | TEXT | Yes | Mode name | No |

| description | TEXT | No | Mode description | No |

| effective\_from | TEXT | Yes | Start date/time | No |

| effective\_to | TEXT | No | End date/time, if applicable | No |

| status | TEXT | Yes | ACTIVE, INACTIVE | No |



Validation: effective\_to must be greater than or equal to effective\_from when supplied.



\### 3.9 alarms



| Field | Type | Required | Validation / allowed values | Unique |

|---|---|---|---|---|

| alarm\_id | TEXT | Yes | Alarm identifier | PK |

| facility\_id | TEXT | Yes | Must reference facilities | No |

| sensor\_id | TEXT | No | Must reference sensors if supplied | No |

| alarm\_type | TEXT | Yes | Alarm category | No |

| severity | TEXT | Yes | LOW, MEDIUM, HIGH, CRITICAL | No |

| description | TEXT | Yes | Alarm description | No |

| detected\_at | TEXT | Yes | Detection timestamp | No |

| status | TEXT | Yes | OPEN, ACKNOWLEDGED, RESOLVED | No |



\### 3.10 simulation\_runs



| Field | Type | Required | Validation / allowed values | Unique |

|---|---|---|---|---|

| simulation\_id | TEXT | Yes | Simulation identifier | PK |

| facility\_id | TEXT | Yes | Must reference facilities | No |

| simulation\_name | TEXT | Yes | Simulation name | No |

| configuration\_json | TEXT | Yes | Required serialized configuration | No |

| assumptions\_json | TEXT | Yes | Required serialized assumptions | No |

| output\_json | TEXT | No | Serialized simulation results | No |

| status | TEXT | Yes | PENDING, COMPLETED, FAILED | No |

| created\_at | TEXT | Yes | Defaults to CURRENT\_TIMESTAMP | No |



\## 4. Supporting entities



\### 4.1 network\_nodes



| Field | Type | Required | Validation |

|---|---|---|---|

| node\_id | TEXT | Yes | Primary key |

| facility\_id | TEXT | Yes | References facilities |

| node\_name | TEXT | Yes | Required name |

| node\_type | TEXT | Yes | PUMP, TANK, VALVE |

| created\_at | TEXT | No | Defaults to CURRENT\_TIMESTAMP |



Unique constraints: facility\_id + node\_name; node\_id + facility\_id.



\### 4.2 simulation\_inputs



| Field | Type | Required | Validation |

|---|---|---|---|

| input\_id | INTEGER | Generated | AUTOINCREMENT primary key |

| simulation\_id | TEXT | Yes | References simulation\_runs |

| parameter\_name | TEXT | Yes | Parameter name |

| original\_value | REAL | No | Original parameter value |

| simulated\_value | REAL | No | Simulated parameter value |

| unit | TEXT | No | Measurement unit |



\### 4.3 equipment\_state\_events



| Field | Type | Required | Validation |

|---|---|---|---|

| event\_id | INTEGER | Generated | AUTOINCREMENT primary key |

| equipment\_type | TEXT | Yes | PUMP, TANK, VALVE, PIPE |

| pump\_id | TEXT | No | References pumps |

| tank\_id | TEXT | No | References tanks |

| valve\_id | TEXT | No | References valves |

| pipe\_id | TEXT | No | References pipes |

| previous\_state | TEXT | No | Previous state |

| new\_state | TEXT | Yes | New state |

| changed\_at | TEXT | Yes | State-change timestamp |

| reason | TEXT | No | Reason for change |



Validation: Exactly one equipment identifier must be supplied.



\### 4.4 ground\_truth



| Field | Type | Required | Validation |

|---|---|---|---|

| truth\_id | INTEGER | Generated | AUTOINCREMENT primary key |

| telemetry\_id | INTEGER | No | References telemetry |

| sensor\_id | TEXT | No | References sensors |

| issue\_type | TEXT | Yes | Known issue category |

| expected\_label | TEXT | Yes | Expected classification |

| scenario\_id | TEXT | Yes | Scenario identifier |

| description | TEXT | No | Scenario description |



Ground truth stores expected labels separately from telemetry input records.



\## 5. Relationship cardinality



| Parent | Child | Cardinality | Optionality |

|---|---|---|---|

| Facility | NetworkNode | 1:N | Each node requires a facility |

| Facility | Pump | 1:N | Each pump requires a facility |

| Facility | Tank | 1:N | Each tank requires a facility |

| Facility | Valve | 1:N | Each valve requires a facility |

| Facility | Pipe | 1:N | Each pipe requires a facility |

| Facility | Sensor | 1:N | Each sensor requires a facility |

| Facility | OperatingMode | 1:N | Each mode requires a facility |

| Facility | Alarm | 1:N | Each alarm requires a facility |

| Facility | SimulationRun | 1:N | Each run requires a facility |

| NetworkNode | Pump | 1:0..1 | Pump node reference required |

| NetworkNode | Tank | 1:0..1 | Tank node reference required |

| NetworkNode | Valve | 1:0..1 | Valve node reference required |

| NetworkNode | Pipe | 1:N | A node may be a source or target |

| Equipment | Sensor | 1:N | Sensor references exactly one equipment category |

| Sensor | Telemetry | 1:N | Each telemetry record requires a sensor |

| Sensor | Alarm | 1:N | Alarm sensor reference is optional |

| SimulationRun | SimulationInput | 1:N | Each input requires a simulation |

| Telemetry | GroundTruth | 1:0..N | Ground-truth telemetry reference is optional |

| Sensor | GroundTruth | 1:0..N | Ground-truth sensor reference is optional |



No explicit many-to-many bridge table is currently defined in the schema.



\## 6. Lifecycle states



\- Facility: ACTIVE, INACTIVE, MAINTENANCE.

\- Pump: ACTIVE, INACTIVE, MAINTENANCE.

\- Tank: ACTIVE, INACTIVE, MAINTENANCE.

\- Pipe: ACTIVE, BLOCKED, MAINTENANCE.

\- Sensor: ACTIVE, FAULTY, INACTIVE.

\- Valve: OPEN, CLOSED, PARTIALLY\_OPEN.

\- OperatingMode: ACTIVE, INACTIVE.

\- Alarm: OPEN, ACKNOWLEDGED, RESOLVED.

\- SimulationRun: PENDING, COMPLETED, FAILED.

\- Telemetry quality: GOOD, SUSPECT, BAD, MISSING.



\## 7. Important validation limitations



The following rules are not fully enforced by the current SQL schema and require application-level validation or additional database constraints:



1\. Tank current\_level must not exceed capacity\_liters.

2\. Sensor and equipment facility IDs must match.

3\. Alarm sensor and facility IDs must match.

4\. Ground-truth telemetry and sensor IDs must match.

5\. Equipment type must match the populated equipment ID in equipment\_state\_events.

6\. Operating-mode effective periods should not overlap where overlapping modes are prohibited.

7\. Alarm deduplication should be handled by the alarm-management workflow.

8\. Lifecycle transitions should be validated by application logic.



\## 8. Units and assumptions



\- Flow: L/min.

\- Volume and tank level: liters.

\- Pipe length: meters.

\- Pipe diameter: millimeters.

\- Opening, speed and leakage: percentage.

\- Pressure: unit must be taken from the actual sensor or master-data source; the schema does not impose a single pressure unit.

\- Timestamps: stored as TEXT; use a consistent ISO 8601 representation.



\## 9. Data provenance



The project uses generated synthetic industrial data. No external industrial dataset is claimed as the source of the generated records. The generator seed, generator version, and generation date should be recorded in the final source manifest.



