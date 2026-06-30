# Phase 3: Hybrid Models — Khalil & Khalil (2023)

**Source paper:** `docs/IJASMArticle.pdf`
**Full summary:** `docs/simulation_summary_khalil_2023.md`
**Depends on:** Phase 1 (Waterfall + Agile baseline), Phase 2 (scaling penalties)
**Goal:** Implement the three hybrid archetypes as new process modes in the FBS ABM
and show that hybrid results bracket between pure Waterfall and pure Agile.

---

## 1. Overview of the Three Hybrid Models

| Model | Description | Key structural difference |
|-------|-------------|--------------------------|
| **Hybrid 1** | Sequential + Iterative phases | Waterfall gates at start/end; Agile sprints in middle |
| **Hybrid 2** | Parallel sub-projects | Two independent agent groups (waterfall + agile) with integration |
| **Hybrid 3** | Mini waterfall cycles (timeboxed) | Full V-cycle per iteration, 8–12 weeks per cycle |

---

## 2. Hybrid Model 1 — Sequential + Iterative

### From the paper
"Decomposing the project into both sequential and iterative phases that integrate
agile practices." Project initiation, requirements, and architectural design are
linear. Detailed design, development, and testing are iterative (agile). Validation
and production are linear again.

### FBS implementation

```
PHASE STRUCTURE:
  [Waterfall gate]  R → F          (Requirements + Architecture — all agents, linear)
        ↓
  [Agile sprints]   F → Be → S     (Design + Development — sub-module teams, iterative)
        ↓
  [Waterfall gate]  S → D          (Integration + Validation — all agents, linear)
```

### Process algorithm

```python
def run_hybrid1(agents, program_structure):
    # Step 1: Waterfall phase — Requirements (R → F), all agents
    waterfall_phase(agents, from_state=R, to_state=F)

    # Step 2: Agile sprints — F → S, sub-module teams in parallel
    for each function in each sub_module:
        agile_sprint(sub_module_team, from_state=F, to_state=S)

    # Step 3: Waterfall phase — Integration (S → D), all agents
    waterfall_phase(agents, from_state=S, to_state=D)

    return collect_metrics()
```

### Expected behavior
- Less upfront documentation cost than pure Waterfall (only R→F is linear)
- Better error detection than pure Waterfall (agile middle catches F→S rework early)
- More overhead than pure Agile (two waterfall sync gates add coordination time)
- Best for: complex projects needing upfront architecture + iterative delivery

---

## 3. Hybrid Model 2 — Parallel Sub-Projects

### From the paper
"Decomposing the project into two independent sub-projects: an agile sub-project and
a traditional sub-project." The traditional team owns final delivery; the agile team
delivers components that integrate into the waterfall product.

### FBS implementation

```
AGENT GROUPS:
  Group A (Traditional): n_waterfall agents → full waterfall R → D
  Group B (Agile):       n_agile agents     → agile sprints R → D on assigned modules

INTEGRATION CHECKPOINT:
  When Group B completes their modules → integration event with Group A
  Integration may trigger Type I reformulations in Group A (coupling)
```

### Parameters
```python
waterfall_fraction = 0.60   # 60% of agents on traditional sub-project
agile_fraction     = 0.40   # 40% of agents on agile sub-project
integration_coupling = 0.15 # probability integration triggers reformulation
```

These defaults reflect the paper's finding that traditional teams "deliver the
intended final product to the customer" while agile teams work on components.

### Process algorithm

```python
def run_hybrid2(agents, split_ratio=0.6):
    waterfall_agents, agile_agents = split_agents(agents, split_ratio)

    # Run in parallel
    waterfall_thread: waterfall_phase(waterfall_agents, R → D)
    agile_thread:     agile_sprints(agile_agents, R → D)

    # Integration event when agile completes
    await agile_thread
    integration_rework = apply_integration_coupling(waterfall_agents)
    await waterfall_thread

    return collect_metrics()
```

### Expected behavior
- Wall-clock time dominated by the slower sub-project (usually waterfall)
- Agile sub-project delivers faster but must wait for waterfall integration
- Integration coupling can trigger significant rework in waterfall agents
- Total effort may be HIGHER than pure approaches (two parallel teams)

---

## 4. Hybrid Model 3 — Mini Waterfall Cycles (Timeboxed)

### From the paper
"The iterations are apparent to mini waterfall cycles. However, the duration of each
cycle is eight to twelve weeks." Each mini-cycle is a complete V/waterfall cycle,
timeboxed at 8–12 weeks. Each cycle delivers a working increment.

### FBS implementation

```
CYCLE STRUCTURE (repeat until all functions complete):
  Each cycle covers a subset of functions
  Within each cycle: full waterfall R → F → Be → S → D
  Cycle length: 8–12 weeks = 320–480 working hours (40h/week)
  At cycle end: integration + retrospective

TERMINATION: all 120 functions have reached state D
```

### Key parameter: functions per cycle
```python
cycle_length_hours  = random.uniform(320, 480)  # 8-12 weeks × 40h
functions_per_cycle = estimate based on team velocity and cycle_length_hours
```

### Timebox enforcement
```python
def run_hybrid3(agents, cycle_hours=400):
    completed_functions = []
    backlog = all_functions.copy()

    while backlog:
        cycle_functions = select_cycle_scope(backlog, cycle_hours, agents)
        cycle_result = waterfall_mini_cycle(agents, cycle_functions, max_time=cycle_hours)

        # Functions not completed within timebox go back to backlog
        completed_functions.extend(cycle_result.completed)
        backlog = cycle_result.incomplete + remaining_backlog

        record_cycle_metrics(cycle_result)

    return aggregate_metrics(completed_functions)
```

### Expected behavior
- Higher overhead than pure Agile (each mini-cycle has waterfall sync gates)
- Better traceability than pure Agile (each cycle has documentation)
- Lower risk than pure Waterfall (failures discovered within 8–12 weeks, not at end)
- Intermediate rework: more than Agile (waterfall within cycle), less than Waterfall (small scope)

---

## 5. Success Factors from Paper (simulation parameters)

| Success factor | Hybrid 1 | Hybrid 2 | Hybrid 3 |
|---------------|----------|----------|----------|
| Stable agile teams | Required | Required (agile group) | Optional |
| Client feedback per iteration | Per sprint | Per agile sprint | Per cycle |
| Timeboxed iterations | Optional | Optional | REQUIRED |
| Cross-team coordination | High | Medium | Low |
| Documentation level | Medium-High | Medium | Medium |

---

## 6. Comparison Targets

After Phase 3, all five process modes should satisfy this ordering for uncoupled software:

```
Time to complete (fastest → slowest):
  Agile < Hybrid 1 ≈ Hybrid 3 < Hybrid 2 < Waterfall

Rework time (least → most):
  Agile < Hybrid 1 < Hybrid 3 < Waterfall < Hybrid 2 (due to integration coupling)

Effort hours (least → most):
  Agile < Hybrid 3 < Hybrid 1 < Waterfall < Hybrid 2
```

These orderings are not from the paper (which is qualitative) but are derived from
first principles of the FBS model and the structural properties of each hybrid.

---

## 7. Files to Add / Modify

| File | Change |
|------|--------|
| `abm/hybrid.py` | `Hybrid1Simulation`, `Hybrid2Simulation`, `Hybrid3Simulation` classes |
| `simulations/run_phase3.py` | Run all 5 process modes, produce comparison table |
| `analysis/plots.py` | Add multi-process bar chart comparison |
| `tests/test_hybrid.py` | Verify ordering of results matches expected hierarchy |
