# Phase 4: AI Coding Dimension (Novel Contribution)

**Depends on:** Phase 1 validated, Phase 3 hybrid models implemented
**Goal:** Model how AI coding assistants change FBS transition dynamics, and how
ReAct-style structured reasoning mitigates AI's stochastic rework risk.

---

## 1. Core Insight: AI as Two Competing Forces

AI coding changes the FBS model in two opposing directions simultaneously:

```
AI effect on designer agent:
  (+) SPEED:       Transition probability per step × speed_multiplier
                   → Agent moves through R→D faster (AI writes/generates quickly)

  (−) UNCERTAINTY: Reformulation probability × uncertainty_multiplier
                   → Agent triggers more rework (AI errors, hallucinations,
                     misaligned requirements, stochastic outputs)
```

The net effect depends on the ratio of speed gain to uncertainty cost:
- If speed dominates: AI helps
- If uncertainty dominates: AI hurts (especially in Waterfall where rework cascades)

---

## 2. AI Mode Parameter Table

| Mode | Speed multiplier | Rework multiplier | Description |
|------|-----------------|-------------------|-------------|
| `NO_AI` | 1.0× | 1.0× | Bott & Mesmer baseline |
| `AI_RAW` | 3–5× | 2–4× | AI coding unmitigated |
| `AI_REACT` | 3–5× | 1.1–1.3× | AI + ReAct uncertainty mitigation |

### Rationale for AI_RAW values
- Speed 3–5×: GitHub Copilot / Claude studies report 35–55% time savings for individual
  coding tasks; for full design cycle including requirements and integration, 3–5× is
  a reasonable upper bound for pure code generation phases.
- Rework 2–4×: AI LLMs are stochastic — same prompt gives different outputs; requirement
  misinterpretation, hallucinated APIs, and integration failures increase reformulation rate.

### Rationale for AI_REACT values
- Speed unchanged: ReAct adds reasoning overhead but doesn't slow the generation itself.
- Rework 1.1–1.3×: ReAct's Reason→Act→Observe loop explicitly checks outputs against
  expected behavior at each FBS gate before committing. This collapses most stochastic
  errors before they become Type I/II reformulations. Residual 10–30% overhead reflects
  cases where ReAct cannot fully resolve uncertainty (ambiguous requirements, novel design).

---

## 3. FBS Implementation of AI Modes

### Agent-level modification

```python
class AIMode(Enum):
    NO_AI    = "no_ai"
    AI_RAW   = "ai_raw"
    AI_REACT = "ai_react"

class FBSAgent:
    def __init__(self, base_matrix, ai_mode=AIMode.NO_AI):
        self.T = base_matrix.copy()
        self.ai_mode = ai_mode
        self._apply_ai_modifiers()

    def _apply_ai_modifiers(self):
        if self.ai_mode == AIMode.NO_AI:
            return  # unchanged

        elif self.ai_mode == AIMode.AI_RAW:
            # Faster forward transitions
            self.T[R, F]  *= AI_SPEED
            self.T[F, Be] *= AI_SPEED
            self.T[Be, S] *= AI_SPEED
            self.T[S, D]  *= AI_SPEED
            # Clip probabilities to [0, 1]
            self.T = np.clip(self.T, 0, 1)

            # Higher reformulation (rework) probabilities
            self.T[S, Be] *= AI_REWORK   # Type 2: structure doesn't match behavior
            self.T[F, R]  *= AI_REWORK   # Type 3: back to requirements
            self.T[S, S]  *= AI_REWORK   # Type 1: within-structure rework

        elif self.ai_mode == AIMode.AI_REACT:
            # Same speed boost
            self.T[R, F]  *= AI_SPEED
            self.T[F, Be] *= AI_SPEED
            self.T[Be, S] *= AI_SPEED
            self.T[S, D]  *= AI_SPEED
            self.T = np.clip(self.T, 0, 1)

            # ReAct reduces rework — minimal increase over baseline
            self.T[S, Be] *= REACT_REWORK   # ~1.1–1.3× (much lower than AI_RAW)
            self.T[F, R]  *= REACT_REWORK
            self.T[S, S]  *= REACT_REWORK
```

### Configuration constants

```python
# abm/config.py

AI_SPEED       = 4.0   # center of 3–5× range
AI_REWORK      = 3.0   # center of 2–4× range (unmitigated AI)
REACT_REWORK   = 1.2   # center of 1.1–1.3× range (ReAct mitigated)

# Sensitivity analysis ranges
AI_SPEED_RANGE    = (3.0, 5.0)
AI_REWORK_RANGE   = (2.0, 4.0)
REACT_REWORK_RANGE= (1.1, 1.3)
```

---

## 4. ReAct Mechanism in FBS Terms

ReAct = **Re**ason → **Act** → **Ob**serve loop applied before each FBS state transition.

### Mapping to FBS gates

| FBS gate | ReAct action |
|----------|-------------|
| R → F | AI reasons about requirements completeness before generating functions |
| F → Be | AI checks generated functions against requirements (observes alignment) |
| Be → S | AI verifies expected behavior is achievable before generating structure |
| S → D | AI runs structural verification against expected behavior before documenting |

At each gate, ReAct catches ~70–90% of misalignments that would otherwise become
Type I/II reformulations. This is modeled by multiplying the reformulation probability
by `REACT_REWORK` instead of `AI_REWORK`.

### Why this matters most for Waterfall

In Waterfall, a Type I reformulation at the S→D gate (CDR) forces ALL agents to
potentially re-do work (phase synchronization). The cascade effect means:

```
Waterfall rework cost = reformulation_probability × n_agents × avg_phase_duration
```

AI_RAW dramatically amplifies this cascade. ReAct specifically targets this gate,
reducing cascade rework by ~70%.

In Agile, rework is caught per-sprint at small scope, so the cascade is bounded.
ReAct helps less in Agile because Agile already bounds rework naturally.

---

## 5. Why Waterfall + AI + ReAct May Win

The hypothesis mechanism:

```
Waterfall + AI + ReAct advantages:
  1. Comprehensive upfront planning at AI speed (3-5× faster R→F phase)
  2. Architecture is fully specified before any implementation begins
     → no mid-sprint architectural changes (Agile's biggest hidden cost)
  3. ReAct at each phase gate eliminates most cascade rework
  4. AI generates implementation from spec deterministically
     → less integration rework than Agile's incremental integration

Agile + AI disadvantages (that Agile's design was solving):
  1. Agile's core value = early error detection via iteration
     → AI can predict most errors upfront → iterations less valuable
  2. Sprint planning overhead × n_sprints × n_teams remains
     → this overhead is NOT reduced by AI
  3. Inter-sprint integration still requires synchronization
  4. Backlog grooming and prioritization overhead unchanged
```

**The tipping point:** When AI reduces FBS uncertainty to the point where the
waterfall cascade risk equals the agile sprint overhead cost, Waterfall breaks even.
Beyond that (with ReAct), Waterfall wins on total effort.

---

## 6. Sensitivity Analysis

Run a 2D parameter sweep to find the tipping point:

```python
for ai_speed in np.linspace(1.0, 6.0, 20):
    for ai_rework in np.linspace(1.0, 5.0, 20):
        for react_rework in [1.0, 1.1, 1.2, 1.3, 1.5]:
            run_all_5_process_modes(ai_speed, ai_rework, react_rework)
            record_winner()
```

**Output:** Phase diagram showing which process mode wins as a function of
(AI speed gain, AI rework increase, ReAct effectiveness).

---

## 7. Files to Add

| File | Content |
|------|---------|
| `abm/ai_layer.py` | `AIMode` enum, AI modifier application, `AI_SPEED`, `AI_REWORK` constants |
| `abm/react_layer.py` | `ReActGate` class: pre-transition verification, rework probability reduction |
| `abm/config.py` | All tunable constants, sensitivity analysis ranges |
| `simulations/run_phase4.py` | 3-way comparison (NO_AI / AI_RAW / AI_REACT) × 5 process modes |
| `simulations/run_sensitivity.py` | 2D parameter sweep → phase diagram |
| `analysis/plots.py` | Phase diagram heatmap, 3-way comparison bars |
| `tests/test_ai_layer.py` | AI modifier applied correctly, probabilities clamped to [0,1] |
| `tests/test_react_layer.py` | ReAct reduces rework vs AI_RAW, not vs NO_AI baseline |

---

## 8. Key Output: Phase 4 Table

```
Process Mode    │ NO_AI effort │ AI_RAW effort │ AI_REACT effort │ Winner vs Agile+AI
────────────────┼──────────────┼───────────────┼─────────────────┼───────────────────
Waterfall       │   37,038 h   │    ?          │      ?          │   ?
Agile           │   21,518 h   │    ?          │      ?          │  (baseline)
Hybrid 1        │     ?        │    ?          │      ?          │   ?
Hybrid 2        │     ?        │    ?          │      ?          │   ?
Hybrid 3        │     ?        │    ?          │      ?          │   ?
```

The "?" values are the novel contribution of this study.
Hypothesis: `Waterfall AI_REACT effort < Agile AI_RAW effort`.
