# Research Roadmap: ABM Simulation of Software Development Efficiency

## Core Research Question

> **Does Waterfall + AI coding (with ReAct risk mitigation) outperform Agile + AI coding?**

**Hypothesis:** AI eliminates Agile's key advantage (early error detection via iteration) by
making upfront planning fast and cheap. Waterfall's sequential structure lets AI plan
comprehensively — provided AI's stochastic rework risk is bounded by structured reasoning
(ReAct pattern). Without mitigation, AI accumulates uncertainty across waterfall phases,
making unmitigated AI+Waterfall worse than Agile+AI.

---

## Document Index

| Document | Phase | Status |
|----------|-------|--------|
| [phase1_foundation.md](phase1_foundation.md) | Reproduce Bott & Mesmer (2019) ABM | TODO |
| [phase2_large_scale.md](phase2_large_scale.md) | Large-scale calibration (Matcha & Kumar 2025) | TODO |
| [phase3_hybrid.md](phase3_hybrid.md) | Hybrid models (Khalil & Khalil 2023) | TODO |
| [phase4_ai_coding.md](phase4_ai_coding.md) | AI coding dimension (novel contribution) | TODO |
| [phase5_full_comparison.md](phase5_full_comparison.md) | Full 15-scenario comparison matrix | TODO |

---

## Full Scenario Matrix (Phase 5 target)

```
                  │ No AI │ AI (raw) │ AI + ReAct │
──────────────────┼───────┼──────────┼────────────┤
Waterfall         │  W0   │   W-AI   │  W-AI-R    │ ← Hypothesis: W-AI-R wins overall
Agile             │  A0   │   A-AI   │  A-AI-R    │
Hybrid 1          │  H1-0 │  H1-AI   │  H1-AI-R   │
Hybrid 2          │  H2-0 │  H2-AI   │  H2-AI-R   │
Hybrid 3          │  H3-0 │  H3-AI   │  H3-AI-R   │
```

15 scenarios × 3 metrics (time, effort, rework) × 10,000 Monte Carlo runs each.

---

## Paper Sources

| Paper | Role in Study |
|-------|--------------|
| Bott & Mesmer (2019) — `systems-07-00037-v2.pdf` | Core ABM framework (FBS Markov agents) |
| Khalil & Khalil (2023) — `IJASMArticle.pdf` | Three hybrid model archetypes |
| Matcha & Kumar (2025) — `in_Jqst_Jan_Mar_2025...pdf` | Large-scale Agile KPIs and scaling penalties |

See `docs/simulation_summary_bott_mesmer_2019.md` and `docs/simulation_summary_khalil_2023.md`
for pre-extracted simulation parameters.

---

## Project Structure (target)

```
software_development_abm/
├── abm/
│   ├── agent.py            # FBS Markov agent
│   ├── waterfall.py        # Waterfall process orchestration
│   ├── agile.py            # Agile (Scrum) process orchestration
│   ├── hybrid.py           # Hybrid 1/2/3 process orchestration
│   ├── ai_layer.py         # AI coding modifier (speed + uncertainty)
│   ├── react_layer.py      # ReAct uncertainty mitigation
│   └── metrics.py          # Metrics collection + Monte Carlo runner
├── simulations/
│   ├── run_phase1.py       # Phase 1: software program baseline
│   ├── run_phase2.py       # Phase 2: large-scale calibration
│   ├── run_phase3.py       # Phase 3: hybrid models
│   ├── run_phase4.py       # Phase 4: AI coding dimension
│   └── run_phase5.py       # Phase 5: full 15-scenario matrix
├── analysis/
│   ├── plots.py            # Histograms, comparison tables
│   └── statistics.py       # Anderson-Darling, mean/SD, ratio tables
├── tests/
│   ├── test_agent.py
│   ├── test_waterfall.py
│   ├── test_agile.py
│   ├── test_hybrid.py
│   ├── test_ai_layer.py
│   └── test_metrics.py
├── results/                # Output CSVs and PNG figures (gitignored if large)
├── docs/
│   ├── roadmap/            # This directory
│   ├── simulation_summary_bott_mesmer_2019.md
│   └── simulation_summary_khalil_2023.md
└── main.py
```

---

## Implementation Schedule

| Phase | Deliverable | Validation Gate |
|-------|-------------|-----------------|
| 1 | FBS ABM + Waterfall/Agile + 10k MC | Match Bott & Mesmer Table 2 within 5% |
| 2 | Large-scale penalties + team-size sensitivity | Agile advantage shrinks with team size |
| 3 | Hybrid 1/2/3 process modes | Hybrid results bracket Waterfall/Agile |
| 4 | AI speed/uncertainty modifier + ReAct | W-AI-R shows reduced rework vs W-AI |
| 5 | Full matrix + final paper-style tables | Hypothesis confirmed or refuted |
