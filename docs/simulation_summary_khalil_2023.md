# Summary: Khalil & Khalil (2023)
**"Combining Agile and Plan-Driven Methodologies for Managing Complex IT Projects: Towards Three Hybrid Models"**
*Int. J. Agile Systems and Management, Vol. 16, No. 1, pp. 124–144 — file: IJASMArticle.pdf*

---

## Purpose in This Project

This is a **qualitative** study (not a simulation). It provides conceptual grounding for why hybrid models matter and defines three hybrid model archetypes that could be used to extend the Bott & Mesmer ABM beyond pure Agile vs. Waterfall.

---

## Key Findings: Three Hybrid Models

### Hybrid Model 1 — Sequential + Iterative Phases
- Project initiation, requirements, and architectural design done **linearly (waterfall)**
- Detailed design, development, and testing done **iteratively (agile/scrum)**
- Validation and production done linearly again
- **Best for:** Long projects (2–3 years), high criticality, high innovation, embedded systems, multiple autonomous teams

### Hybrid Model 2 — Parallel Agile + Traditional Sub-Projects
- Project split into two **independent** sub-projects: one agile team, one waterfall team
- Agile deliverables integrated into the waterfall product
- **Best for:** Large matrix organizations with separate agile and traditional teams

### Hybrid Model 3 — Mini Traditional Cycles (Timeboxed Waterfall Sprints)
- Iterative cycles of 8–12 weeks each, but each cycle follows a mini-waterfall/V-cycle structure
- Each mini-cycle is timeboxed
- **Best for:** Teams that need traceability but want shorter delivery cadence

---

## Key Parameters for ABM Simulation Extension

| Dimension | Waterfall | Agile | Hybrid 1 | Hybrid 2 | Hybrid 3 |
|-----------|-----------|-------|----------|----------|----------|
| Planning up-front | Full | Minimal | Partial | Full (traditional sub-project) | Per cycle |
| Iteration length | None | 10–30 days | Sprint-based | Sprint-based (agile part) | 8–12 weeks |
| Synchronization | Phase gates | None | Phase gates + sprints | Integration points | Cycle end |
| Documentation | Extensive | Minimal | Moderate | Moderate | Moderate |
| Feedback loops | Late | Continuous | Per sprint | Per agile sprint | Per cycle |

---

## Factors Affecting Hybrid Model Choice

- **Project size** — larger projects favor more structure
- **Project criticality** — safety-critical systems need documentation (hybrid 1 or 3)
- **Innovation level** — high innovation favors agile portions
- **Team autonomy** — autonomous teams favor agile
- **Traceability requirements** — regulatory needs push toward waterfall phases

---

## Relevance to ABM

To simulate hybrid models using Bott & Mesmer's FBS framework:
- **Hybrid 1:** Use waterfall FBS logic for R→F and S→D phases; agile sprints for F→S middle phases
- **Hybrid 2:** Run separate waterfall and agile agent groups; define integration checkpoints
- **Hybrid 3:** Implement timeboxed waterfall cycles (8–12 week maximum per mini-V-cycle)
