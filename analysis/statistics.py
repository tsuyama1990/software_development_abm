"""
Statistical analysis functions for Phase 5.

BLUEPRINT:
Data Flow:
- Takes numeric lists (samples) from simulation results.
- Computes statistical tests (t-test, normality) and effect sizes (Cohen's d).
- Formats outputs as strings or dictionaries for reporting.

Module Boundaries:
- Pure functions, no side effects.
- Inputs: sequences of floats.
- Outputs: floats, booleans, and dictionaries containing test results.
"""

import math
from collections.abc import Sequence
from typing import Any

import numpy as np
from scipy import stats


def normality_test(samples: Sequence[float]) -> dict[str, float]:
    """
    Perform Shapiro-Wilk test for normality.

    Args:
        samples: Sequence of numeric values.

    Returns:
        dict with 'statistic' and 'p_value'.

    """
    if len(samples) < 3:
        return {"statistic": float("nan"), "p_value": float("nan")}

    # Shapiro-Wilk can take max 5000 samples, so we sample down if too large
    if len(samples) > 5000:
        rng = np.random.default_rng(seed=42)
        test_samples = [float(x) for x in rng.choice(samples, size=5000, replace=False)]
    else:
        test_samples = list(samples)

    stat, p = stats.shapiro(test_samples)
    return {"statistic": stat, "p_value": p}


def t_test(a: Sequence[float], b: Sequence[float]) -> dict[str, float]:
    """
    Perform independent two-sample t-test (Welch's, unequal variances).

    Args:
        a: First sequence of numeric values.
        b: Second sequence of numeric values.

    Returns:
        dict with 'statistic' and 'p_value'.

    """
    if len(a) < 2 or len(b) < 2:
        return {"statistic": float("nan"), "p_value": float("nan")}

    stat, p = stats.ttest_ind(a, b, equal_var=False)
    return {"statistic": stat, "p_value": p}


def cohens_d(a: Sequence[float], b: Sequence[float]) -> float:
    """
    Calculate Cohen's d effect size between two groups.

    Formula: d = (mean(a) - mean(b)) / pooled_sd

    Args:
        a: First sequence of numeric values.
        b: Second sequence of numeric values.

    Returns:
        Cohen's d as a float.

    """
    n1, n2 = len(a), len(b)
    if n1 < 2 or n2 < 2:
        return float("nan")

    # Means
    mean1 = sum(a) / n1
    mean2 = sum(b) / n2

    # Variances (sample variance)
    var1 = sum((x - mean1) ** 2 for x in a) / (n1 - 1)
    var2 = sum((x - mean2) ** 2 for x in b) / (n2 - 1)

    # Pooled standard deviation
    pooled_sd = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))

    if pooled_sd == 0:
        return 0.0

    return (mean1 - mean2) / pooled_sd


def hypothesis_test_waterfall_react_vs_agile_raw(
    w_react_effort: Sequence[float],
    g_raw_effort: Sequence[float],
) -> dict[str, Any]:
    """
    Test the core hypothesis: E(W-C) < E(G-B).

    H0: E(W-C) >= E(G-B)
    H1: E(W-C) < E(G-B)

    Since we want to test if W-C is LESS than G-B, this is a one-tailed test.

    Args:
        w_react_effort: Effort samples for Waterfall+AI_REACT.
        g_raw_effort: Effort samples for Agile+AI_RAW.

    Returns:
        Dictionary containing hypothesis test results.

    """
    # Two-tailed t-test
    ttest_res = t_test(w_react_effort, g_raw_effort)
    stat = ttest_res["statistic"]
    p_two_tailed = ttest_res["p_value"]

    # Convert to one-tailed p-value for H1: mean(W-C) < mean(G-B)
    # If stat is negative, the mean of the first group is less than the second
    p_one_tailed = p_two_tailed / 2.0 if stat < 0 else 1.0 - p_two_tailed / 2.0

    is_significant = p_one_tailed < 0.05

    mean_w = sum(w_react_effort) / len(w_react_effort) if w_react_effort else 0
    mean_g = sum(g_raw_effort) / len(g_raw_effort) if g_raw_effort else 0

    diff_pct = ((mean_w - mean_g) / mean_g * 100) if mean_g else 0.0

    return {
        "statistic": stat,
        "p_value": p_one_tailed,
        "is_significant": is_significant,
        "mean_w_react": mean_w,
        "mean_g_raw": mean_g,
        "pct_difference": diff_pct,
        "cohens_d": cohens_d(w_react_effort, g_raw_effort),
        "hypothesis_confirmed": is_significant and stat < 0,
    }

