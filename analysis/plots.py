"""
Plotting utilities for Phase 1 simulation results.

BLUEPRINT:
Data Flow:
- Takes raw arrays of total_time, effort_hours, and rework_time.
- Generates histograms mimicking Figures 9-14 from Bott & Mesmer 2019.
- Saves plots as PNG files to the root directory.

Module Boundaries:
- Inputs: Simulation metrics lists.
- Outputs: Saved matplotlib PNG figures.
"""

from collections.abc import Sequence
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def plot_scaling_curve(
    results: list[dict[str, float]],
    filename: str = "scaling_curve.png",
) -> None:
    """
    Plot the scaling curve of team sizes versus Agile advantage.

    Args:
        results: List of dictionaries containing scaling simulation results.
        filename: Output filename for the PNG image.

    """
    team_sizes = [r["n_submodule_teams"] for r in results]
    advantages = [r["agile_advantage"] for r in results]

    plt.figure(figsize=(10, 6))
    plt.plot(team_sizes, advantages, marker="o", linestyle="-", color="b", linewidth=2)

    plt.axhline(1.0, color="red", linestyle="--", linewidth=2, label="Parity (Advantage = 1.0)")

    plt.title("Agile Advantage vs. Team Size (Phase 2)", fontsize=14)
    plt.xlabel("Number of Sub-module Teams", fontsize=12)
    plt.ylabel("Agile Advantage (Waterfall Time / Agile Time)", fontsize=12)
    plt.grid(visible=True, linestyle="--", alpha=0.7)
    plt.legend()

    # Adjust y-axis limits to clearly show erosion if applicable
    min_adv = min(advantages) if advantages else 0
    max_adv = max(advantages) if advantages else 2
    plt.ylim(max(0, min_adv - 0.5), max_adv + 0.5)

    plt.tight_layout()
    plt.savefig(filename)
    plt.close()


def plot_multi_process_comparison(
    metrics_dict: dict[str, dict[str, float]],
    filename: str = "phase3_comparison.png",
) -> None:
    """
    Plot a multi-process bar chart comparison for Phase 3.

    Args:
        metrics_dict: A dictionary mapping process mode names (e.g., 'Agile')
            to their metrics dictionaries (containing 'time', 'effort', 'rework').
        filename: Output filename for the PNG image.

    """
    labels = list(metrics_dict.keys())

    # We want grouped bar charts for Time, Effort, Rework
    times = [metrics_dict[L].get("time", 0.0) for L in labels]
    efforts = [metrics_dict[L].get("effort", 0.0) for L in labels]
    reworks = [metrics_dict[L].get("rework", 0.0) for L in labels]

    x = range(len(labels))
    width = 0.25

    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Time and Rework on primary Y-axis
    ax1.bar([i - width for i in x], times, width, label="Time (h)", color="skyblue")
    ax1.bar(list(x), reworks, width, label="Rework (h)", color="salmon")

    ax1.set_xlabel("Process Mode", fontsize=12)
    ax1.set_ylabel("Time / Rework (hours)", fontsize=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=11)

    # Effort on secondary Y-axis (since it's usually an order of magnitude larger)
    ax2 = ax1.twinx()
    ax2.bar([i + width for i in x], efforts, width, label="Total Effort (h)", color="lightgreen")
    ax2.set_ylabel("Total Effort (hours)", fontsize=12)

    # Title and Legend
    plt.title("Phase 3: Multi-Process Comparison", fontsize=14)

    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper left")

    fig.tight_layout()
    plt.savefig(filename)
    plt.close(fig)


def plot_3way_comparison(
    metrics_dict: dict[str, dict[str, float]],
    filename: str = "phase4_comparison.png",
) -> None:
    """
    Plot a multi-process bar chart comparison for Phase 4 (NO_AI vs AI_RAW vs AI_REACT).

    Expects metrics_dict to have process mode keys, and values are dicts with AIMode keys.
    """
    labels = list(metrics_dict.keys())
    no_ai = [metrics_dict[L].get("no_ai", 0.0) for L in labels]
    ai_raw = [metrics_dict[L].get("ai_raw", 0.0) for L in labels]
    ai_react = [metrics_dict[L].get("ai_react", 0.0) for L in labels]

    x = np.arange(len(labels))
    width = 0.25

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.bar(x - width, no_ai, width, label="NO_AI", color="lightgray")
    ax.bar(x, ai_raw, width, label="AI_RAW", color="salmon")
    ax.bar(x + width, ai_react, width, label="AI_REACT", color="skyblue")

    ax.set_xlabel("Process Mode", fontsize=12)
    ax.set_ylabel("Total Effort (hours)", fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)

    plt.title("Phase 4: AI Mode Comparison Across Processes", fontsize=14)
    ax.legend()

    fig.tight_layout()
    plt.savefig(filename)
    plt.close(fig)


def plot_phase_diagram(
    results: list[dict[str, float | str]],
    filename: str = "phase4_diagram.png",
) -> None:
    """
    Plot the phase diagram from a parameter sweep.

    results should have ai_speed, ai_rework, and winner.
    """
    speeds = sorted({float(r["ai_speed"]) for r in results})
    reworks = sorted({float(r["ai_rework"]) for r in results})

    z_matrix = np.zeros((len(speeds), len(reworks)))

    for r in results:
        i = speeds.index(float(r["ai_speed"]))
        j = reworks.index(float(r["ai_rework"]))
        z_matrix[i, j] = 1 if r["winner"] == "Waterfall" else 0

    plt.figure(figsize=(8, 6))

    # Let's plot with extent to show actual axes
    plt.imshow(
        z_matrix.T,
        origin="lower",
        extent=(min(speeds), max(speeds), min(reworks), max(reworks)),
        aspect="auto",
        cmap=plt.cm.coolwarm,
    )

    plt.colorbar(ticks=[0, 1], label="Winner (0=Agile, 1=Waterfall)")
    plt.title("Phase Diagram: AI Speed vs Rework Penalty", fontsize=14)
    plt.xlabel("AI Speed Multiplier", fontsize=12)
    plt.ylabel("AI Rework Multiplier", fontsize=12)

    plt.tight_layout()
    plt.savefig(filename)
    plt.close()


def plot_histogram(
    data: Sequence[float],
    title: str,
    xlabel: str,
    filename: str,
    color: str = "skyblue",
) -> None:
    """
    Plot and save a histogram of simulation results.

    Args:
        data: Sequence of numeric values to plot.
        title: Title of the chart.
        xlabel: Label for the X axis.
        filename: Output filename for the PNG image.
        color: Bar color.

    """
    plt.figure(figsize=(10, 6))
    plt.hist(data, bins=30, color=color, edgecolor="black", alpha=0.7)

    # Calculate mean to add a vertical line
    mean_val = sum(data) / len(data) if data else 0
    plt.axvline(
        mean_val,
        color="red",
        linestyle="dashed",
        linewidth=2,
        label=f"Mean: {mean_val:,.0f}",
    )

    plt.title(title, fontsize=14)
    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel("Frequency (Number of Runs)", fontsize=12)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.legend()

    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

def plot_rework_fraction(
    metrics_dict: dict[str, dict[str, float]],
    filename: str = "phase5_rework_fraction.png",
) -> None:
    """
    Plot a stacked bar chart of productive vs rework time.

    Args:
        metrics_dict: dict mapping scenario name to metrics containing 'time' and 'rework'.
        filename: Output filename for the PNG image.

    """
    labels = list(metrics_dict.keys())

    times = [metrics_dict[L].get("time", 0.0) for L in labels]
    reworks = [metrics_dict[L].get("rework", 0.0) for L in labels]

    productive = [t - r for t, r in zip(times, reworks, strict=False)]

    fig, ax = plt.subplots(figsize=(14, 7))

    x = range(len(labels))

    ax.bar(x, productive, label="Productive Time (h)", color="lightgreen")
    ax.bar(x, reworks, bottom=productive, label="Rework Time (h)", color="salmon")

    ax.set_xlabel("Scenario", fontsize=12)
    ax.set_ylabel("Total Time (hours)", fontsize=12)
    ax.set_xticks(list(x))
    # Rotate labels for better readability if many
    ax.set_xticklabels(labels, fontsize=10, rotation=45, ha="right")

    plt.title("Rework Fraction by Scenario", fontsize=14)
    ax.legend()

    fig.tight_layout()
    plt.savefig(filename)
    plt.close(fig)


def plot_hypothesis_test(
    w_react_effort: Sequence[float],
    g_raw_effort: Sequence[float],
    p_value: float,
    diff_pct: float,
    filename: str = "phase5_hypothesis_test.png",
) -> None:
    """
    Plot overlapping histograms of W-C and G-B effort.

    Args:
        w_react_effort: List of effort values for W-C.
        g_raw_effort: List of effort values for G-B.
        p_value: The calculated p-value.
        diff_pct: Percentage difference in means.
        filename: Output filename for the PNG image.

    """
    plt.figure(figsize=(10, 6))

    plt.hist(w_react_effort, bins=40, alpha=0.5, label="Waterfall+AI_REACT (W-C)", color="skyblue")
    plt.hist(g_raw_effort, bins=40, alpha=0.5, label="Agile+AI_RAW (G-B)", color="salmon")

    w_mean = sum(w_react_effort) / len(w_react_effort) if w_react_effort else 0
    g_mean = sum(g_raw_effort) / len(g_raw_effort) if g_raw_effort else 0

    plt.axvline(
        w_mean, color="blue", linestyle="dashed", linewidth=2, label=f"W-C Mean: {w_mean:,.0f}",
    )
    plt.axvline(
        g_mean, color="red", linestyle="dashed", linewidth=2, label=f"G-B Mean: {g_mean:,.0f}",
    )

    plt.title("Core Hypothesis Test: Effort (W-C vs G-B)", fontsize=14)
    plt.xlabel("Total Effort (hours)", fontsize=12)
    plt.ylabel("Frequency", fontsize=12)

    # Add text box with stats
    textstr = f"p-value: {p_value:.4e}\nDifference: {diff_pct:+.1f}%"
    props = {"boxstyle": "round", "facecolor": "wheat", "alpha": 0.5}
    plt.gca().text(0.05, 0.95, textstr, transform=plt.gca().transAxes, fontsize=12,
                   verticalalignment="top", bbox=props)

    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    plt.tight_layout()
    plt.savefig(filename)
    plt.close()


def plot_final_figures(
    results_dict: dict[str, dict[str, float]], output_dir: str = "results/figures",
) -> None:
    """
    Generate all Phase 5 figures based on the results dictionary.

    Args:
        results_dict: A dictionary mapping scenario names like 'W-C', 'G-B', 'H1-A'
            to their metrics (mean_time, mean_effort, mean_rework).
        output_dir: Directory to save the PNGs.

    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Format the data for plot_3way_comparison (AI Impact)
    # Target format: {'Waterfall': {'no_ai': X, 'ai_raw': Y, 'ai_react': Z}, ...}
    ai_impact_data_effort: dict[str, dict[str, float]] = {}

    # We will map standard codes to labels
    codes = {
        "W": "Waterfall",
        "G": "Agile",
        "H1": "Hybrid 1",
        "H2": "Hybrid 2",
        "H3": "Hybrid 3",
    }

    ai_codes = {
        "A": "no_ai",
        "B": "ai_raw",
        "C": "ai_react",
    }

    for pm_code, pm_name in codes.items():
        ai_impact_data_effort[pm_name] = {}
        for ai_code, ai_name in ai_codes.items():
            scenario = f"{pm_code}-{ai_code}"
            if scenario in results_dict:
                ai_impact_data_effort[pm_name][ai_name] = results_dict[scenario].get("effort", 0.0)

    plot_3way_comparison(
        ai_impact_data_effort, filename=str(Path(output_dir) / "fig2_ai_impact.png"),
    )

    # Format for Rework fraction
    rework_data = {}
    for scenario, metrics in results_dict.items():
        rework_data[scenario] = {
            "time": metrics.get("time", 0.0),
            "rework": metrics.get("rework", 0.0),
        }

    plot_rework_fraction(rework_data, filename=str(Path(output_dir) / "fig6_rework_fraction.png"))

    # Note: Figure 1 (Baseline), Figure 4 (Phase), Figure 5 (Scaling) are
    # expected to be generated via their respective phase scripts or
    # run_phase5.py if it loads that data. The instructions primarily
    # ask to have these functions available.

    # Figure 3 (Hypothesis) is handled separately since it needs raw sample data,
    # not just means. run_phase5.py will call plot_hypothesis_test directly.

