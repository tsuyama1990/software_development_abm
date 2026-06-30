"""Tests for the plotting utilities."""

from pathlib import Path

from analysis.plots import plot_histogram, plot_multi_process_comparison, plot_scaling_curve


def test_plot_multi_process_comparison() -> None:
    """Ensure plot_multi_process_comparison executes and creates a file."""
    metrics = {
        "Agile": {"time": 100.0, "effort": 500.0, "rework": 20.0},
        "Waterfall": {"time": 200.0, "effort": 400.0, "rework": 50.0},
    }
    filename = Path("test_multi_process.png")

    plot_multi_process_comparison(metrics, filename=str(filename))

    assert filename.exists()
    filename.unlink()


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
