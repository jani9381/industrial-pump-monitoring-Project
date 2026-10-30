def is_sensor_fault_mislabeled(issue_type: str, predicted_label: str) -> bool:
    """
    Return True when a known sensor fault has been assigned
    a process/equipment fault label.

    Rule:
    - Sensor-related issue types must have SENSOR-related labels.
    - Other issue types are not evaluated by this rule.
    """

    if not issue_type or not predicted_label:
        raise ValueError("Issue type and predicted label are required.")

    issue = issue_type.strip().upper()
    label = predicted_label.strip().upper()

    is_sensor_issue = "SENSOR" in issue
    has_sensor_label = "SENSOR" in label

    return is_sensor_issue and not has_sensor_label
