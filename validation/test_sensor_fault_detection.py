import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent)
)

from engines.sensor_fault_simulator import simulate_sensor_fault
from engines.sensor_fault_detection import detect_sensor_fault


test_cases = [
    ("Sensor Drift", "SENSOR_DRIFT"),
    ("Sensor Stuck", "SENSOR_STUCK"),
    ("Sensor Noise", "SENSOR_NOISE"),
]

all_passed = True

for fault_name, expected in test_cases:

    data = simulate_sensor_fault(
        baseline=50.0,
        duration=60,
        fault_type=fault_name,
        severity=20,
        noise_level=1.0,
        random_seed=42
    )

    result = detect_sensor_fault(data)

    passed = result["fault_type"] == expected
    all_passed = all_passed and passed

    print("\n------------------------------")
    print("Test:", fault_name)
    print("Expected:", expected)
    print("Detected:", result["fault_type"])
    print("Confidence:", result["confidence"])
    print("Message:", result["message"])
    print("Result:", "PASS" if passed else "FAIL")


print("\n==============================")

if all_passed:
    print("ALL SENSOR FAULT DETECTION TESTS PASSED")
else:
    print("SOME TESTS FAILED")
