# Industrial Pump Monitoring System

## Overview

A Python-based industrial pump monitoring application for monitoring facilities, equipment and sensor telemetry. It provides anomaly detection, alarm management, pump simulation, mass balance analysis, sensor fault simulation and diagnostic visualization.

The system uses synthetic industrial data to demonstrate equipment monitoring, abnormal operating condition detection and operating-change simulation.

## Features

- Multi-facility industrial equipment monitoring
- Pump, tank, valve, pipe and sensor management
- Synthetic telemetry generation
- Anomaly detection and fault classification
- Alarm creation and status management
- Pump operation simulation
- Mass balance calculations
- Sensor drift, stuck and noise simulation
- Heuristic sensor fault detection
- FastAPI REST API
- Streamlit interactive dashboard
- SQLite database
- CSV, JSON and SQL database exports
- Data validation and reproducibility checks

## Technology Stack

- Python
- SQLite
- Pandas and NumPy
- SciPy and Scikit-learn
- FastAPI and Uvicorn
- Streamlit and Plotly
- NetworkX
- Pytest

## Project Setup (Windows)

### Prerequisites

- Windows 10 or Windows 11
- Python 3.10 or later
- PowerShell

### 1. Open the project directory

```powershell
cd path\to\industrial-pump-monitoring
```

### 2. Create a virtual environment

```powershell
py -m venv venv
```

If the `py` command is unavailable, use your installed Python executable.

### 3. Install dependencies

PowerShell activation is not required. Use the virtual environment's Python executable directly:

```powershell
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

This approach also works when PowerShell script execution policies prevent virtual-environment activation.

## Run the REST API

Open the first PowerShell terminal in the project directory.

Start the FastAPI backend:

```powershell
.\venv\Scripts\python.exe -m uvicorn api.routes:app --reload --host 127.0.0.1 --port 8000
```

API base URL:

http://127.0.0.1:8000

API documentation:

http://127.0.0.1:8000/docs

Health endpoint:

http://127.0.0.1:8000/health

Keep this terminal running while using the dashboard.

## Run the Dashboard

Open a second PowerShell terminal in the project directory.

Start the Streamlit application:

```powershell
.\venv\Scripts\python.exe -m streamlit run app.py --server.port 8502
```

Open the dashboard:

http://localhost:8502

The FastAPI backend must be running before using dashboard features that retrieve data from the API.

## Run Automated Tests

Execute the automated test suite:

```powershell
.\venv\Scripts\python.exe -m pytest tests/ -v
```

Latest verified result: 17 tests passed.

## Validation Utilities

Run the data validation utility:

```powershell
.\venv\Scripts\python.exe validation\validate_data.py
```

Run relationship validation:

```powershell
.\venv\Scripts\python.exe validation\validate_relationships.py
```

Run reproducibility validation:

```powershell
.\venv\Scripts\python.exe validation\test_reproducibility.py
```

Run export verification:

```powershell
.\venv\Scripts\python.exe validation\verify_exports.py
```

These utilities inspect generated data, relationships, reproducibility and exported database files.

## Database and Exports

The SQLite database is located at:

```text
data/industrial_monitoring.db
```

Database exports are located in:

```text
data/exports/
```

The export directory contains CSV and JSON exports for the database tables, a complete SQL dump and an export manifest containing SHA-256 checksums.

## Synthetic Data and Evaluation

The application uses generated telemetry and controlled synthetic fault scenarios across three sample facilities.

The baseline dataset contains 100,000 GOOD telemetry records, with an additional 240 SUSPECT fault-injection records.

The evaluation dataset contains injected fault records. Reported detection results describe performance on those controlled scenarios and should not be interpreted as guaranteed real-world performance.

## Known Limitations

- The pump simulation uses simplified linear flow assumptions.
- The simulation is not a full hydraulic network solver.
- Detailed pump curves, pressure dynamics and pipe friction losses are not modeled.
- Fault classification relies primarily on sensor and equipment mappings.
- Leak and blockage scenarios are currently grouped under pipeline flow anomalies.
- Sensor faults can be classified as equipment anomalies.
- Sensor fault detection uses heuristic rules; confidence scores are not calibrated probabilities.
- Equipment state event history is not currently populated by the application.
- Alarm history contains repeated records for individual anomalous telemetry readings.

## Project Validation Summary

- Automated tests: 17 passed.
- Negative scenario tests: 5 passed.
- Data validation: passed.
- Relationship validation: passed.
- Reproducibility validation: passed.
- CSV and JSON export validation: passed.
- SQL restore and SQLite integrity validation: passed.
- Foreign-key violations in restored database: 0.

## Troubleshooting (Windows)

### Python command not found

Use the virtual environment's Python executable:

```powershell
.\venv\Scripts\python.exe
```

### PowerShell activation is blocked

Activation is optional. Run Python and its modules directly:

```powershell
.\venv\Scripts\python.exe -m pip
```

### Streamlit command not found

Use:

```powershell
.\venv\Scripts\python.exe -m streamlit run app.py --server.port 8502
```

### API connection error

Check that the FastAPI backend is running on port 8000 before opening the dashboard.

### Missing database or application data

Ensure `data/industrial_monitoring.db` exists and contains the required application tables and records before starting the application.