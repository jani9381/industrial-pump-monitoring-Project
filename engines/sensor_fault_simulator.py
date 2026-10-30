
import numpy as np
import pandas as pd


def simulate_sensor_fault(
    baseline=50.0,
    duration=60,
    fault_type="Sensor Drift",
    severity=20,
    noise_level=1.0,
    random_seed=42
):
    """
    Generate synthetic normal and faulty sensor readings.

    This simulator does not modify the production database.
    """

    if duration < 2:
        raise ValueError("Duration must be at least 2 readings.")

    if severity < 0:
        raise ValueError("Severity cannot be negative.")

    rng = np.random.default_rng(random_seed)

    timestamps = np.arange(duration)

    normal_noise = rng.normal(
        loc=0,
        scale=noise_level,
        size=duration
    )

    normal_readings = baseline + normal_noise

    faulty_readings = normal_readings.copy()

    fault_start = duration // 3

    if fault_type == "Sensor Drift":

        drift = np.linspace(
            0,
            severity,
            duration - fault_start
        )

        faulty_readings[fault_start:] += drift

    elif fault_type == "Sensor Stuck":

        stuck_value = faulty_readings[fault_start]

        faulty_readings[fault_start:] = stuck_value

    elif fault_type == "Sensor Noise":

        additional_noise = rng.normal(
            loc=0,
            scale=severity,
            size=duration - fault_start
        )

        faulty_readings[fault_start:] += additional_noise

    else:
        raise ValueError(
            "Unsupported fault type. "
            "Choose Sensor Drift, Sensor Stuck or Sensor Noise."
        )

    return pd.DataFrame({
        "timestamp": timestamps,
        "normal_reading": normal_readings,
        "faulty_reading": faulty_readings,
        "fault_status": [
            "NORMAL" if i < fault_start else "FAULT"
            for i in timestamps
        ]
    })


if __name__ == "__main__":

    result = simulate_sensor_fault(
        baseline=50,
        duration=60,
        fault_type="Sensor Drift",
        severity=20
    )

    print("\nSENSOR FAULT SIMULATION")
    print("=======================")
    print(result.head(10))
    print("\nTotal readings:", len(result))
    print("Fault readings:", (result["fault_status"] == "FAULT").sum())
    print("Normal readings:", (result["fault_status"] == "NORMAL").sum())
