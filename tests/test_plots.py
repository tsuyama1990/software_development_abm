"""Tests for the plotting utilities."""

from pathlib import Path

from analysis.plots import plot_histogram, plot_scaling_curve


def test_plot_scaling_curve_writes_file() -> None:
    """Ensure plot_scaling_curve executes and creates a file."""
    results = [
        {"n_submodule_teams": 4.0, "agile_advantage": 1.5},
        {"n_submodule_teams": 8.0, "agile_advantage": 1.2},
    ]
    filename = Path("test_scaling_curve.png")

    plot_scaling_curve(results, filename=str(filename))

    assert filename.exists()
    filename.unlink()


def test_plot_histogram_writes_file() -> None:
    """Ensure plot_histogram executes and creates a file."""
    data = [1.0, 2.0, 2.0, 3.0]
    filename = Path("test_hist.png")

    plot_histogram(data, "Title", "XLabel", str(filename))

    assert filename.exists()
    filename.unlink()
