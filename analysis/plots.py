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

import matplotlib.pyplot as plt


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
        mean_val, color="red", linestyle="dashed", linewidth=2, label=f"Mean: {mean_val:,.0f}",
    )

    plt.title(title, fontsize=14)
    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel("Frequency (Number of Runs)", fontsize=12)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.legend()

    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
