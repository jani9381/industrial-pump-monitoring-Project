
from engines.mass_balance import calculate_mass_balance


def test_balanced_flow():
    result = calculate_mass_balance(
        inlet_flow=150,
        outlet_flow=120,
        storage_change=30
    )

    assert result["net_imbalance_lpm"] == 0
    assert result["status"] == "BALANCED"


def test_input_exceeds_output():
    result = calculate_mass_balance(
        inlet_flow=150,
        outlet_flow=100,
        storage_change=20
    )

    assert result["net_imbalance_lpm"] == 30
    assert result["status"] == "INPUT_EXCEEDS_OUTPUT"


def test_output_exceeds_input():
    result = calculate_mass_balance(
        inlet_flow=100,
        outlet_flow=130,
        storage_change=0
    )

    assert result["net_imbalance_lpm"] == -30
    assert result["status"] == "OUTPUT_EXCEEDS_INPUT"


def test_invalid_duration():
    try:
        calculate_mass_balance(100, 80, 20, 0)
        assert False, "Expected ValueError"
    except ValueError:
        assert True
