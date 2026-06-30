# Phase 5: Full Comparison Matrix

**Depends on:** All previous phases complete
**Goal:** Run all 15 scenarios, produce the final paper-quality comparison tables
and figures, and test the core research hypothesis.

---

## 1. Full Scenario Matrix

```
                  │ NO_AI (A) │ AI_RAW (B) │ AI_REACT (C) │
──────────────────┼───────────┼────────────┼──────────────┤
Waterfall    (W)  │   W-A     │    W-B     │    W-C       │  ← Hypothesis: W-C wins
Agile        (G)  │   G-A     │    G-B     │    G-C       │
Hybrid 1     (H1) │  H1-A     │   H1-B     │   H1-C       │
Hybrid 2     (H2) │  H2-A     │   H2-B     │   H2-C       │
Hybrid 3     (H3) │  H3-A     │   H3-B     │   H3-C       │
```

15 scenarios × 3 metrics × 10,000 Monte Carlo runs each = **450,000 simulation runs total**.

At 4 processes with ~30ms per run (estimated): ~3.75 hours wall time.
Parallelize across CPU cores using `multiprocessing.Pool`.

---

## 2. Metrics Collected Per Scenario

| Metric | Symbol | Unit | Definition |
|--------|--------|------|-----------|
| Total time to complete | `T` | hours | Wall-clock from start to all agents reaching D |
| Total effort hours | `E` | hours | Sum of all agent-hours across all time steps |
| Time in rework | `RW` | hours | Hours spent on reformulation-triggered tasks |
| Productivity | `P` | func/h | 120 functions / `E` |
| Rework fraction | `RF` | % | `RW / T × 100` |

For each metric: `mean`, `std`, `min`, `max`, `p5`, `p95`.

---

## 3. Hypothesis Test Structure

### Primary hypothesis
```
H0: E(W-C) ≥ E(G-B)   [Waterfall+AI+ReAct uses same or more effort than Agile+AI]
H1: E(W-C) < E(G-B)   [Waterfall+AI+ReAct uses LESS effort than Agile+AI]
```

Test: two-sample t-test on the 10,000 Monte Carlo run effort values.
Significance level: α = 0.05.

### Secondary hypotheses
```
H_time:   T(W-C) < T(G-B)   [Waterfall+AI+ReAct is faster]
H_rework: RW(W-C) < RW(G-B) [Waterfall+AI+ReAct has less rework]
H_hybrid: min(H1-C, H2-C, H3-C) < W-C  [A hybrid beats pure Waterfall+AI+ReAct]
```

The last hypothesis tests whether a hybrid model (Waterfall structure + Agile sprints
+ AI + ReAct) can do even better than pure Waterfall+AI+ReAct.

---

## 4. Expected Results (Hypothesis-Driven Predictions)

These are predictions BEFORE running the simulation. The simulation confirms or refutes.

### Effort hours ranking (predicted, best to worst)
```
1.  W-C   (Waterfall + AI + ReAct)      ← hypothesis winner
2.  H1-C  (Hybrid 1 + AI + ReAct)       ← may tie W-C
3.  G-C   (Agile + AI + ReAct)
4.  G-B   (Agile + AI_RAW)              ← Agile naturally bounds rework
5.  H3-C  (Hybrid 3 + AI + ReAct)
6.  H1-B  (Hybrid 1 + AI_RAW)
7.  W-B   (Waterfall + AI_RAW)          ← WORST: full cascade rework from AI uncertainty
```

### Why W-B (Waterfall + AI_RAW) is predicted worst
AI without ReAct in Waterfall creates a "rework cascade catastrophe":
- High uncertainty from AI → high reformulation probability at CDR
- All 101 agents must wait and redo work (global sync)
- The cascade is multiplicative across all 120 functions
- Total rework >> pure Waterfall baseline

### Why G-B (Agile + AI_RAW) is better than W-B
Agile naturally bounds rework per sprint. AI's stochastic errors are caught within
one sprint scope (typically 1 function), not cascaded across all 120 functions.

### Why W-C beats G-B
ReAct at each FBS gate reduces cascade probability to near-baseline level.
Waterfall's parallel planning (all teams plan from the same complete spec) means
less total reformulation than Agile's incremental discovery process.

---

## 5. Output Figures

### Figure 1: Baseline comparison (NO_AI) — reproduces Bott & Mesmer Table 2
- Histograms: Waterfall time, Agile time (Figures 9, 10 of paper)
- Bar chart: 5 process modes × 3 metrics

### Figure 2: AI impact — NO_AI vs AI_RAW vs AI_REACT per process mode
- 5×3 subplot grid
- Each subplot: 3 bars (one per AI mode) for one metric × one process mode

### Figure 3: Hypothesis test visualization
- Overlapping histograms: W-C effort vs G-B effort distributions
- Annotate with p-value and % difference in means

### Figure 4: Phase diagram (sensitivity analysis)
- X-axis: AI speed multiplier (1× → 6×)
- Y-axis: AI rework multiplier (1× → 5×)
- Color: which process mode wins (Waterfall, Agile, or best Hybrid)
- Separate panels for NO_REACT and WITH_REACT

### Figure 5: Team-size scaling (from Phase 2)
- X-axis: number of sub-module teams (4 → 50)
- Y-axis: Agile vs Waterfall time ratio (1.0 = equal, <1.0 = Agile faster)
- Lines: NO_AI, AI_RAW, AI_REACT

### Figure 6: Rework fraction by scenario
- Stacked bar chart: productive time vs rework time for all 15 scenarios
- Shows visually that W-B has catastrophic rework, W-C has minimal rework

---

## 6. Final Summary Table (paper-ready)

```
Scenario      │ Effort (h)  │ Time (h)  │ Rework (h)  │ vs G-A baseline
──────────────┼─────────────┼───────────┼─────────────┼────────────────
W-A (baseline)│ 37,038      │ 2,012     │ 1,693       │  +72% effort
G-A (baseline)│ 21,518      │   765     │   724       │  reference
W-B           │   TBD       │   TBD     │   TBD       │  TBD
G-B           │   TBD       │   TBD     │   TBD       │  TBD
W-C           │   TBD       │   TBD     │   TBD       │  TBD  ← HYPOTHESIS
G-C           │   TBD       │   TBD     │   TBD       │  TBD
H1-C          │   TBD       │   TBD     │   TBD       │  TBD
H2-C          │   TBD       │   TBD     │   TBD       │  TBD
H3-C          │   TBD       │   TBD     │   TBD       │  TBD
```

---

## 7. Files to Add

| File | Content |
|------|---------|
| `simulations/run_phase5.py` | All 15 scenarios, parallel execution via multiprocessing |
| `analysis/plots.py` | All 6 figures above |
| `analysis/statistics.py` | t-tests, Anderson-Darling, effect size (Cohen's d) |
| `results/phase5_summary.csv` | Full results table (all means, SDs, ratios) |
| `results/figures/` | All PNG figures |
| `tests/test_phase5.py` | Verify ordering constraints hold: W-C < G-B (effort) |

---

## 8. Execution Plan

```python
# simulations/run_phase5.py (pseudocode)

from multiprocessing import Pool

scenarios = [
    (process_mode, ai_mode)
    for process_mode in [WATERFALL, AGILE, HYBRID1, HYBRID2, HYBRID3]
    for ai_mode in [NO_AI, AI_RAW, AI_REACT]
]

with Pool(processes=cpu_count()) as pool:
    results = pool.map(run_scenario_10k, scenarios)

# Aggregate and export
df = build_results_dataframe(results)
df.to_csv("results/phase5_summary.csv")
generate_all_figures(df)
run_hypothesis_tests(df)
```

---

## 9. Deliverable: Research Conclusions

The simulation will produce one of three outcomes:

**Outcome A — Hypothesis confirmed:**
`E(W-C) < E(G-B)` at p < 0.05
→ Conclusion: AI coding with ReAct makes Waterfall competitive with or superior to
  Agile+AI for software development efficiency.

**Outcome B — Hypothesis partially confirmed:**
`T(W-C) < T(G-B)` but `E(W-C) ≥ E(G-B)`
→ Conclusion: Waterfall+AI+ReAct is faster to market but uses more total effort.
  Depends on whether the organization values speed or cost more.

**Outcome C — Hypothesis refuted:**
`E(W-C) ≥ E(G-B)` and `T(W-C) ≥ T(G-B)`
→ Conclusion: Agile's incremental error-bounding advantage persists even with AI+ReAct.
  The best Hybrid model (H1-C or H3-C) may be the winner instead.

All three outcomes are scientifically valid and publishable. The simulation design
is sound regardless of which outcome emerges.
