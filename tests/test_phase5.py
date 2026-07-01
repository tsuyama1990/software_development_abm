"""
Tests for Phase 5 components (statistics and constraints).

BLUEPRINT:
Data Flow:
- Uses mock or synthetic data for stats module testing.
- Uses minimal simulation runs to check basic ordering constraints.
- Validates return types and behaviors of analysis functions.
"""


import csv
import math
from pathlib import Path

import numpy as np

from abm.config import AIMode
from analysis.statistics import (
    cohens_d,
    hypothesis_test_waterfall_react_vs_agile_raw,
    normality_test,
    t_test,
)
from simulations.run_phase5 import main, run_all_scenarios, run_scenario


def test_t_test() -> None:
    """Test t-test function with simple data."""
    group_a = [1.0, 2.0, 1.5, 2.5, 2.0]
    group_b = [5.0, 6.0, 5.5, 6.5, 6.0]

    result = t_test(group_a, group_b)

    assert "statistic" in result
    assert "p_value" in result
    assert result["statistic"] < 0  # Mean A is less than Mean B
    assert result["p_value"] < 0.05  # Significantly different


def test_t_test_insufficient_data() -> None:
    """Test t-test with insufficient data."""
    group_a = [1.0]
    group_b = [5.0]

    result = t_test(group_a, group_b)

    # Should return nan
    assert math.isnan(result["statistic"])
    assert math.isnan(result["p_value"])


def test_normality_test() -> None:
    """Test Shapiro-Wilk test with simple data."""
    rng = np.random.default_rng(42)
    # Generate normal data
    data = list(rng.normal(0, 1, 100))

    result = normality_test(data)

    assert "statistic" in result
    assert "p_value" in result
    # Usually p > 0.05 for normal data
    assert result["p_value"] > 0.05


def test_cohens_d() -> None:
    """Test Cohen's d effect size."""
    group_a = [1.0, 2.0, 3.0]
    group_b = [1.0, 2.0, 3.0]

    d = cohens_d(group_a, group_b)
    assert d == 0.0  # Identical groups have 0 effect size

    group_c = [4.0, 5.0, 6.0]
    d2 = cohens_d(group_a, group_c)
    assert d2 < 0.0  # Mean A < Mean C


def test_hypothesis_test_waterfall_react_vs_agile_raw() -> None:
    """Test the core hypothesis test function."""
    # Suppose Waterfall+REACT effort is significantly less than Agile+RAW
    w_react = [100.0, 105.0, 95.0, 102.0, 98.0]
    g_raw = [200.0, 210.0, 190.0, 205.0, 195.0]

    result = hypothesis_test_waterfall_react_vs_agile_raw(w_react, g_raw)

    assert bool(result["is_significant"]) is True
    assert bool(result["hypothesis_confirmed"]) is True
    assert result["mean_w_react"] == 100.0
    assert result["mean_g_raw"] == 200.0
    assert result["pct_difference"] == -50.0
    assert result["statistic"] < 0
    assert result["cohens_d"] < 0


def test_run_all_scenarios_and_main() -> None:
    """Test that we can run all phase 5 scenarios with 1 MC run and output a CSV."""
    # Run simulation function
    all_results, w_react, g_raw = run_all_scenarios(1)

    assert len(all_results) == 15
    assert "W-C" in all_results
    assert "G-B" in all_results

    assert len(w_react) == 1
    assert len(g_raw) == 1

    # Run the main execution wrapper
    main(1)

    # Check outputs exist
    csv_file = Path("results/phase5_summary.csv")
    assert csv_file.exists()

    # Check CSV format
    with csv_file.open("r") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == [
            "Scenario",
            "Effort (h)",
            "Time (h)",
            "Rework (h)",
            "Productivity (func/h)",
            "Rework Fraction (%)",
        ]
        rows = list(reader)
        assert len(rows) == 15

    # Check that Figures are generated
    fig_dir = Path("results/figures")
    assert (fig_dir / "fig2_ai_impact.png").exists()
    assert (fig_dir / "fig3_hypothesis_test.png").exists()
    assert (fig_dir / "fig6_rework_fraction.png").exists()


def test_run_scenario() -> None:
    """Test the run_scenario sub-function to increase coverage."""
    res_w = run_scenario("Waterfall", AIMode.NO_AI, 0)
    assert "total_time" in res_w

    res_a = run_scenario("Agile", AIMode.NO_AI, 0)
    assert "total_time" in res_a

    res_h1 = run_scenario("Hybrid1", AIMode.NO_AI, 0)
    assert "total_time" in res_h1

    res_h2 = run_scenario("Hybrid2", AIMode.NO_AI, 0)
    assert "total_time" in res_h2

    res_h3 = run_scenario("Hybrid3", AIMode.NO_AI, 0)
    assert "total_time" in res_h3

