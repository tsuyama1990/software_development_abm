"""Tests for the plotting utilities."""

from pathlib import Path

from analysis.plots import (
    plot_3way_comparison,
    plot_final_figures,
    plot_histogram,
    plot_hypothesis_test,
    plot_multi_process_comparison,
    plot_phase_diagram,
    plot_rework_fraction,
    plot_scaling_curve,
)


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


def test_plot_3way_comparison() -> None:
    metrics = {
        "Waterfall": {"no_ai": 100.0, "ai_raw": 200.0, "ai_react": 150.0},
        "Agile": {"no_ai": 80.0, "ai_raw": 90.0, "ai_react": 70.0},
    }
    filename = Path("test_3way.png")
    plot_3way_comparison(metrics, str(filename))
    assert filename.exists()
    filename.unlink()


def test_plot_phase_diagram() -> None:
    results: list[dict[str, float | str]] = [
        {"ai_speed": 1.0, "ai_rework": 1.0, "winner": "Agile"},
        {"ai_speed": 2.0, "ai_rework": 2.0, "winner": "Waterfall"},
    ]
    filename = Path("test_phase.png")
    plot_phase_diagram(results, str(filename))
    assert filename.exists()
    filename.unlink()


def test_plot_rework_fraction() -> None:
    metrics = {
        "W-A": {"time": 100.0, "rework": 20.0},
        "G-B": {"time": 80.0, "rework": 10.0},
    }
    filename = Path("test_rework.png")
    plot_rework_fraction(metrics, str(filename))
    assert filename.exists()
    filename.unlink()


def test_plot_hypothesis_test() -> None:
    w_effort = [100.0, 110.0]
    g_effort = [120.0, 130.0]
    filename = Path("test_hyp.png")
    plot_hypothesis_test(w_effort, g_effort, 0.05, -10.0, str(filename))
    assert filename.exists()
    filename.unlink()


def test_plot_final_figures() -> None:
    results = {
        "W-A": {"time": 100.0, "effort": 500.0, "rework": 20.0},
        "W-B": {"time": 110.0, "effort": 550.0, "rework": 30.0},
        "W-C": {"time": 90.0, "effort": 450.0, "rework": 10.0},
    }
    out_dir = Path("test_figs")
    plot_final_figures(results, str(out_dir))
    assert (out_dir / "fig2_ai_impact.png").exists()
    assert (out_dir / "fig6_rework_fraction.png").exists()
    for f in out_dir.iterdir():
        f.unlink()
    out_dir.rmdir()
