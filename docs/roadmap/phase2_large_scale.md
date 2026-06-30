# Phase 2: Large-Scale Calibration — Matcha & Kumar (2025)

**Source paper:** `docs/in_Jqst_Jan_Mar_2025_GC250237-AP05-...pdf`
**Depends on:** Phase 1 baseline complete and validated
**Goal:** Add empirically grounded scaling penalties so that Agile advantage shrinks
as team size grows, matching real-world survey observations.

---

## 1. What Phase 2 Adds to the Phase 1 Model

Phase 1 assumes ideal conditions: zero communication overhead, perfect coordination,
and uniform Agile consistency across teams. Phase 2 relaxes these assumptions using
data from the Matcha & Kumar (2025) large-scale Agile survey.

### New parameters introduced

| Parameter | Survey finding | ABM implementation |
|-----------|---------------|-------------------|
| Coordination overhead | 33.33% of teams struggle with cross-team coordination | Add sync delay proportional to team count |
| Communication barrier | 36.67% report barriers (time zones, distributed teams) | Add random delay per inter-agent communication event |
| Resistance to change | 20.00% resistance from leadership/employees | Slow FBS transitions for a random 20% of agents |
| Agile consistency gap | Teams diverge in practices across large orgs | Add variance to sprint velocity per team |
| Dependency management | 30.00% struggle with managing inter-team dependencies | Add coupling weight between module teams |

---

## 2. Coordination Overhead Model

In Phase 1, waterfall sync gates have zero cost. In Phase 2, sync has a cost
proportional to the number of teams that must coordinate.

```
coordination_delay = base_delay × (n_teams / n_teams_baseline) × coordination_rate

Where:
  base_delay          = 0 in Phase 1
  n_teams_baseline    = 12 (software sim from Phase 1)
  coordination_rate   = 0.3333 (survey: 33% of teams affected)
```

For Agile, the coordination cost applies at sprint review meetings:
```
sprint_review_cost = n_dependent_teams × inter_team_meeting_hours
```

For Waterfall, coordination cost applies at each phase gate:
```
phase_gate_cost = n_total_teams × gate_review_hours
```

---

## 3. Communication Barrier Model

36.67% of large Agile projects report communication barriers as significant obstacles.

Model: at each inter-agent information transfer event, apply a delay drawn from:
```
delay ~ Bernoulli(0.3667) × Uniform(low_delay, high_delay)
```

This affects:
- Agile: daily scrum information flow between teams
- Waterfall: requirements cascade from program lead → module leads → sub-module teams
- Hybrid models: integration checkpoints

**Effect:** Agents in affected teams have effectively slower transition rates through
the FBS model, since they receive delayed information about design decisions.

---

## 4. Resistance-to-Change Model

20% of respondents report resistance to Agile adoption from leadership/employees.
In a team undergoing waterfall-to-agile transition, some agents are slower.

```
resistant_agent_fraction = 0.20
resistant_speed_factor   = 0.60  # 40% slower transition probabilities
```

Randomly assign `resistant_agent_fraction` of agents at simulation start.
Their FBS transition matrix is multiplied by `resistant_speed_factor`.

This penalty applies **only to Agile and Hybrid simulations**, not pure Waterfall,
reflecting the real-world friction of adopting new practices.

---

## 5. Team-Size Sensitivity Study

Run Phase 1 simulations across a range of team sizes to produce a scaling curve:

```
n_submodule_teams ∈ [4, 8, 12, 20, 32, 50]
```

For each team count, apply the scaling penalties above and record:
- Agile efficiency ratio vs Waterfall (time, effort, rework)
- How much the Agile advantage erodes as scale increases

**Expected result:** At small scale (4 teams), Agile advantage ≈ Phase 1 results.
At large scale (50 teams), Agile advantage shrinks significantly due to coordination
and communication costs.

---

## 6. KPI Mapping to FBS Metrics

Matcha & Kumar (2025) measure success via three KPIs. Map to FBS simulation outputs:

| Paper KPI | FBS simulation metric | Survey finding |
|-----------|----------------------|---------------|
| Time-to-Market | `total_time` | 55% report significant improvement with Agile |
| Product Quality | `rework_time` (lower = higher quality) | 50% report improvement |
| Customer Satisfaction | Proxy: `1 - (rework_time / total_time)` | 60% report improvement |

---

## 7. Framework Effectiveness Weights

From survey Table (Effectiveness of Agile Frameworks):

| Framework | Very Effective | Effective | Combined |
|-----------|---------------|-----------|---------|
| Scrum | 25% | 45% | 70% |
| SAFe | 35% | 40% | 75% |
| Kanban | 20% | 35% | 55% |

Use these as **velocity modifiers** for the team-level sprint performance in Agile
and hybrid simulations:

```
scrum_velocity_modifier = 0.70
safe_velocity_modifier  = 0.75
kanban_velocity_modifier= 0.55
```

Default Phase 1 uses `scrum_velocity_modifier = 1.0` (ideal conditions).
Phase 2 applies the realistic modifier.

---

## 8. Files to Add / Modify

| File | Change |
|------|--------|
| `abm/scaling.py` | `ScalingPenalties` class: coordination, communication, resistance |
| `abm/agent.py` | Add `is_resistant` flag, `communication_delay` attribute |
| `abm/agile.py` | Apply scaling penalties during sprint and scrum phases |
| `abm/waterfall.py` | Apply gate review cost, requirements cascade delay |
| `simulations/run_phase2.py` | Team-size sweep + scaling curves |
| `analysis/plots.py` | Add scaling curve plots (Agile advantage vs team size) |
| `tests/test_scaling.py` | Verify penalties reduce Agile advantage monotonically with scale |

---

## 9. Validation Targets for Phase 2

| Observation | Expected simulation behavior |
|-------------|----------------------------|
| Coordination is #1 barrier (33%) | Agile advantage in time drops >10% at 32+ teams |
| Communication barriers (37%) | SD of total_time increases with team size for Agile |
| 70% Scrum effectiveness | Agile time advantage in sim ≈ 70% of ideal-conditions result |
| Scrum > Kanban for large teams | Scrum modifier gives better KPIs than Kanban modifier |
