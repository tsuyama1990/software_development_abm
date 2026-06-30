# Simulation Summary: Bott & Mesmer (2019)
**"Agent-Based Simulation of Hardware-Intensive Design Teams Using the Function–Behavior–Structure Framework"**
*Systems 2019, 7, 37 — file: systems-07-00037-v2.pdf*

---

## 1. Core Agent Model: FBS (Function–Behavior–Structure)

**States:** R (Requirements) → F (Functions) → Be (Expected Behavior) → Bs (Behavior of Structure) / S (Structure) → D (Documentation)

**Key simplification:** Bs and S are **collapsed into a single state** so the model is a valid first-order Markov chain (the path F→Bs has no return path otherwise).

**Transition mechanics (per time step per agent):**
- Draw a random number; if draw > transition probability → advance to next state
- If draw ≤ probability → stay in current state (still working)
- Reformulations (rework): Type 1 = S back to S; Type 2 = Bs back to Be; Type 3 = back to R from any state

**Agent model is a 5×5 transition probability matrix** stored per agent. Each agent has slightly different probabilities drawn from a distribution around the mean calibrated values.

**Calibration source:** Aerospace design data (ref [42]: Bott & Mesmer, AIAA 2019). Mean performer + 90% CI high side used to generate individual agent matrices.

**Notional example probabilities (Figure 2 — NOT calibrated values):**
```
R:  self=0.9,  to F=0.1
F:  self=0.2,  to Be=0.8,  type3_rework→R=0.3 (shown separately)
Be/Bs/S: collapsed, self=0.5, to D=0.3, type1/2 rework loops
D:  self=1.0  (absorbing/terminal state)
```
> Actual calibrated probabilities are NOT published in this paper; they come from ref [42].

---

## 2. Software Program Simulation Structure

### Team Hierarchy (Figure 3)
```
Program Lead (1 agent)
├── Module 1 Lead → Sub-modules: 1.1, 1.2, 1.3  (3 teams × 8 designers)
├── Module 2 Lead → Sub-modules: 2.1, 2.2, 2.3  (3 teams × 8 designers)
├── Module 3 Lead → Sub-modules: 3.1, 3.2        (2 teams × 8 designers)
└── Module 4 Lead → Sub-modules: 4.1, 4.2, 4.3, 4.4 (4 teams × 8 designers)
```
- **12 sub-module teams × 8 designers = 96 + 4 module leads + 1 program lead = 101 agents total**
- Each sub-module has **10 functions** to develop → 120 total functions
- **Low coupling** between sub-modules (software assumption: each subsystem independent)
- Team size of 8 matches Scrum recommendations

### Key Assumptions
- Designers modeled by FBS Markov process
- Synthesis + analysis + evaluation collapsed to single activity
- System is unprecedented (no a priori optimal solution)
- Design teams work in parallel; don't wait for other teams
- Reformulations from design incompatibility are Type I only (for software)
- Zero-lag information sharing between agents
- Team leaders do NOT contribute to design work (only planning/integration)
- Idle time not counted toward effort hours

---

## 3. Waterfall Simulation

**Sequential phases (all agents must complete phase before next begins):**
1. **SRR** — Requirements Development: all agents R → F
2. **SFR** — Function Development: all agents F → Be
3. **PDR** — Preliminary Design: lowest-level teams Be → S
4. **CDR** — Detailed Design: lowest-level teams S → D

**Synchronization:** All agents must finish current FBS transition before the group advances.

**Rework occurs** at CDR step when Bs is compared to Be — reformulations loop back.

---

## 4. Agile Simulation

**Phase 1 — Initial Planning:** Program leader + module leaders transition R → F (develops user stories / high-level requirements into functions).

**Phase 2 — Sprints (lowest-level teams):** Each team works through the **full FBS cycle (R → D) for each function serially**, sprint by sprint.
- Sprint length: 10–30 days with daily scrum
- Teams work **in parallel** with no cross-team synchronization at major reviews
- Reformulations added to product backlog; addressed in subsequent sprints
- Product released incrementally as functions complete

**Key difference from waterfall:** No global synchronization checkpoints; teams release incrementally.

---

## 5. Monte Carlo Setup

- **10,000 runs** per simulation (waterfall and agile each)
- Verified: 100-run results within 5% of 10,000-run results
- Same random draws used across both simulations for fairness

---

## 6. Metrics Collected

| Metric | Definition |
|--------|-----------|
| **Total time** | Wall-clock time from start to all agents reaching D |
| **Effort hours** | Sum of all agent-hours expended across all time steps |
| **Rework time** | Time spent on tasks triggered by Type I/II/III reformulations |

Ratios (Agile/Waterfall) computed for each metric to compare methodologies.

---

## 7. Target Results — Software Program (to validate your implementation)

| Metric | Waterfall | Agile | Agile Advantage | Expected Range |
|--------|-----------|-------|-----------------|----------------|
| Effort hours | 37,038 h (SD=1,225) | 21,518 h (SD=1,091) | **−42%** | 36–50% less |
| Total time | 2,012 h (SD=337) | 765 h (SD=157) | **−62%** | 30–70% faster |
| Rework time | 1,693 h (SD=332) | 724 h (SD=157) | **−57%** | ~50% less |

Distribution shape: approximately normal (Anderson–Darling test, 5% significance).

---

## 8. Launch Vehicle Simulation (Hardware-Intensive, Coupled)

Same methodology, but adds **9 design variables with coupling** — choices made by one team can force rework in other teams (Type I reformulations propagate across subsystems).

**Results show coupling dramatically reduces Agile advantage:**

| Metric | Waterfall | Agile | Difference |
|--------|-----------|-------|------------|
| Effort hours | 22,846 h (SD=1,693) | 22,672 h (SD=1,724) | −1% (not significant) |
| Total time | 1,836 h (SD=405) | 1,608 h (SD=407) | −12% |
| Rework time | 1,519 h (SD=402) | 1,569 h (SD=407) | **+3% more** for Agile |

**Conclusion:** Agile benefits are large for uncoupled (software) systems but modest for highly coupled (hardware) systems.

---

## 9. Implementation Checklist

- [ ] FBS Markov agent with 5×5 transition matrix
- [ ] Per-agent matrix drawn from mean ± CI distribution
- [ ] Software hierarchy: 1 program lead + 4 module leads + 12 sub-module teams × 8
- [ ] 10 functions per sub-module (120 total)
- [ ] Waterfall: global phase synchronization (SRR→SFR→PDR→CDR)
- [ ] Agile: initial planning phase + parallel sprints per function
- [ ] Track: total_time, effort_hours, rework_time per run
- [ ] Monte Carlo: 10,000 runs
- [ ] Output histograms + mean/SD summary table

---

## 10. Source Code Reference

Original MATLAB source: https://github.com/monza66/Waterfall-Agile_ABS
