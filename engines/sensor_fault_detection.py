
import numpy as np
import pandas as pd


def detect_sensor_fault(data: pd.DataFrame) -> dict:
    required = ["normal_reading", "faulty_reading"]

    for column in required:
        if column not in data.columns:
            raise ValueError(f"Missing column: {column}")

    if len(data) < 6:
        raise ValueError("At least 6 readings are required.")

    readings = pd.to_numeric(
        data["faulty_reading"], errors="coerce"
    ).dropna().to_numpy(dtype=float)

    if len(readings) < 6:
        raise ValueError("Not enough valid readings.")

    split = max(3, len(readings) // 3)

    baseline = readings[:split]
    observed = readings[split:]

    baseline_std = float(np.std(baseline))
    observed_std = float(np.std(observed))
    baseline_mean = float(np.mean(baseline))

    x = np.arange(len(observed))
    slope = float(np.polyfit(x, observed, 1)[0])

    correlation = 0.0
    if observed_std > 0:
        correlation = float(np.corrcoef(x, observed)[0, 1])
        if not np.isfinite(correlation):
            correlation = 0.0

    drift_amount = abs(float(observed[-1] - observed[0]))

    if observed_std <= max(0.05, baseline_std * 0.05):
        fault_type = "SENSOR_STUCK"
        confidence = 0.99
        message = "Sensor readings are nearly constant."

    elif (
        drift_amount > max(3 * baseline_std, abs(baseline_mean) * 0.03)
        and abs(correlation) >= 0.70
    ):
        fault_type = "SENSOR_DRIFT"
        confidence = 0.90
        message = "Sensor readings show gradual directional change."

    elif observed_std > max(baseline_std * 3, baseline_std + 2):
        fault_type = "SENSOR_NOISE"
        confidence = 0.90
        message = "Sensor readings fluctuate excessively."

    else:
        fault_type = "NORMAL"
        confidence = 0.95
        message = "No significant sensor malfunction detected."

    return {
        "fault_type": fault_type,
        "confidence": confidence,
        "message": message,
        "baseline_mean": round(baseline_mean, 3),
        "baseline_std": round(baseline_std, 3),
        "observed_std": round(observed_std, 3),
        "drift_amount": round(drift_amount, 3),
        "trend_slope": round(slope, 4),
        "trend_correlation": round(correlation, 4),
    }
