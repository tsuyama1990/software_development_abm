"""Plotting utilities for Phase 1 simulation results.

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

import matplotlib.pyplot as plt
import numpy as np


def plot_scaling_curve(
    results: list[dict[str, float]],
    filename: str = "scaling_curve.png",
) -> None:
    """Plot the scaling curve of team sizes versus Agile advantage.

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
    """Plot a multi-process bar chart comparison for Phase 3.

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
    """Plot a multi-process bar chart comparison for Phase 4 (NO_AI vs AI_RAW vs AI_REACT).

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
    """Plot the phase diagram from a parameter sweep.

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
    """Plot and save a histogram of simulation results.

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
