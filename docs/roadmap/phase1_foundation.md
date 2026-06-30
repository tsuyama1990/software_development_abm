# Phase 1: Foundation — Reproduce Bott & Mesmer (2019)

**Source paper:** `docs/systems-07-00037-v2.pdf`
**Full summary:** `docs/simulation_summary_bott_mesmer_2019.md`
**Validation target:** Match paper Table 2 results within 5%

---

## 1. Agent Model: FBS Markov Process

### States (5 effective states after collapse)
```
R  →  F  →  [Be/Bs]  →  S  →  D
Req   Func   Behavior    Str   Doc
```
Bs and S are **collapsed into one state** so the model is a valid first-order Markov chain.
D is the absorbing (terminal) state.

### Transition Matrix (5×5 per agent)
Each agent holds a personal matrix `T[i,j]` where i = current state, j = next state.
Probabilities are drawn per-agent from a distribution: mean calibrated value ± 90% CI.

```python
# States enum
R, F, Be, S, D = 0, 1, 2, 3, 4

# Example structure (NOT calibrated values — see note below)
T = np.array([
    [p_RR, p_RF, 0,    0,    0   ],  # from R
    [p_FR, p_FF, p_FBe,0,    0   ],  # from F  (p_FR = Type 3 reformulation)
    [0,    0,    p_BB, p_BS, 0   ],  # from Be (p_BB includes Type 2 rework loop)
    [0,    0,    p_SB, p_SS, p_SD],  # from S  (p_SB = Type 1 reformulation)
    [0,    0,    0,    0,    1.0 ],  # from D  (absorbing)
])
```

> **Note on calibration:** The actual calibrated probabilities come from Bott & Mesmer
> AIAA 2019 (ref [42] in the paper), not published in this paper. We reverse-engineer
> approximate values that reproduce the paper's output metrics. Starting point: use the
> notional Figure 2 values and tune until simulated means match Table 2 within 5%.

### Per-agent matrix generation
```
mean_T  = calibrated mean transition matrix
high_T  = 90th percentile performer matrix
Each agent i:  T_i = mean_T + rand() * (high_T - mean_T)
```

### Time step mechanics
Each time step = 1 working hour. Per step per agent:
- Draw `u ~ Uniform(0,1)`
- If `u > T[current_state, next_state]` → advance to next state
- Else → stay (still working on current state)
- If reformulation triggered → set back to earlier state; increment rework counter

---

## 2. Team and Program Structure

### Software Program (101 agents total)

```
Level 0:  Program Lead          (1 agent)
Level 1:  Module Leads          (4 agents, one per module)
Level 2:  Sub-module Teams      (12 teams × 8 designers = 96 agents)

Modules and sub-modules:
  Module 1: sub-modules 1.1, 1.2, 1.3
  Module 2: sub-modules 2.1, 2.2, 2.3
  Module 3: sub-modules 3.1, 3.2
  Module 4: sub-modules 4.1, 4.2, 4.3, 4.4

Each sub-module: 10 functions to develop
Total functions: 12 × 10 = 120
```

### Agent roles
- **Program/Module leads:** Participate in planning phases only; do NOT do design work
- **Sub-module team designers:** Do the actual FBS design work
- **Team size 8:** Matches Scrum recommendations

### Coupling assumption (software)
Low coupling: sub-module designs are independent. One team's structural decisions
do NOT trigger reformulations in other teams. (Contrast with Phase 1b launch vehicle.)

---

## 3. Waterfall Simulation

### Process flow
All agents advance through phases sequentially. No agent starts the next phase
until ALL agents in the program have completed the current phase.

```
Phase       FBS transition    Milestone   Who participates
─────────────────────────────────────────────────────────
Requirements   R → F          SRR         All agents (top-down flow)
Functions      F → Be         SFR         All agents (top-down flow)
Prelim Design  Be → S         PDR         Sub-module teams only
Detail Design  S → D          CDR         Sub-module teams only
```

### Per-phase algorithm
```
while not all_agents_in_state(next_state):
    for each agent not yet in next_state:
        attempt_transition(agent)
    time_step += 1
    record_metrics()
```

### Rework in waterfall
Rework occurs primarily at CDR (S→D transition): the behavior of the structure
is compared to expected behavior. If mismatch → Type I or II reformulation.
Reformulated agents must redo work; other agents wait (waterfall synchronization).

---

## 4. Agile Simulation

### Process flow

**Phase A — Initial planning** (program lead + module leads only):
- All planning-level agents transition R → F
- Represents: user story creation, backlog population

**Phase B — Sprints** (sub-module teams, all in parallel):
- Each team works through full R → D cycle for each of their 10 functions
- Functions developed serially within a team, teams run in parallel
- Sprint length: 10–30 time steps (random per sprint)
- Reformulations go to product backlog; addressed in next sprint
- No cross-team synchronization — each team releases independently

### Per-sprint algorithm
```
for each function f in sub_module.functions:
    while agent not in state D:
        attempt_transition(agent, f)
        time_step_local += 1
        if reformulation: add_to_backlog(f)
    process_backlog()
```

### Parallelism
All 12 sub-module teams run their sprint loops simultaneously.
Wall-clock time = max(team_completion_times).

---

## 5. Metrics Collection

```python
class RunMetrics:
    total_time: float        # wall-clock hours from start to last agent reaching D
    effort_hours: float      # sum of all agent-hours expended (all time steps × agents)
    rework_time: float       # hours spent on reformulation-triggered tasks
```

After 10,000 runs:
```python
mean(total_time), std(total_time)
mean(effort_hours), std(effort_hours)
mean(rework_time), std(rework_time)
ratio_agile_waterfall = agile_mean / waterfall_mean  # for each metric
```

---

## 6. Validation Targets (Table 2 from paper)

| Metric | Waterfall | Agile | Agile vs Waterfall |
|--------|-----------|-------|-------------------|
| Effort hours | 37,038 h (SD=1,225) | 21,518 h (SD=1,091) | −42% |
| Total time | 2,012 h (SD=337) | 765 h (SD=157) | −62% |
| Rework time | 1,693 h (SD=332) | 724 h (SD=157) | −57% |

Histogram shapes: approximately normal (Anderson–Darling test at 5%).
Distribution of total_time for waterfall: range roughly 1,000–3,000 h.
Distribution of total_time for agile: range roughly 400–1,200 h.

---

## 7. Files to Implement

| File | Content |
|------|---------|
| `abm/agent.py` | `FBSAgent` class: state, matrix, step(), reformulation logic |
| `abm/waterfall.py` | `WaterfallSimulation`: phase orchestration, sync gates |
| `abm/agile.py` | `AgileSimulation`: planning phase + parallel sprint loops |
| `abm/metrics.py` | `MetricsCollector`, `MonteCarloRunner` (10k runs) |
| `simulations/run_phase1.py` | Build 101-agent software program, run both sims, print Table 2 |
| `analysis/plots.py` | Histograms matching Figures 9–14 of the paper |
| `tests/test_agent.py` | First passage time verification (mean ≈ 1/p) |
| `tests/test_waterfall.py` | Phase synchronization, rework propagation |
| `tests/test_agile.py` | Sprint mechanics, parallel execution |
| `tests/test_metrics.py` | Metric accumulation correctness |

---

## 8. Calibration Strategy

Since exact transition probabilities are not published, use this iterative approach:

1. Start with notional Figure 2 values from paper
2. Run 1,000 MC iterations (fast), check means against Table 2
3. Adjust matrix values using binary search on the key bottleneck transitions
4. Confirm with 10,000 runs and check histogram shapes match paper figures
5. Document final calibrated matrix in `abm/config.py`

Key insight: the ratio Agile/Waterfall is more robust to exact parameter values
than absolute numbers. Prioritize matching the ratios (−42%, −62%, −57%) first.
