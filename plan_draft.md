1.  **Update `abm/config.py`**:
    - Add `is_resistant: bool = False`, `resistant_speed_factor: float = 1.0`, and `velocity_modifier: float = 1.0` to `AgentConfig`.

2.  **Update `abm/agent.py`**:
    - Modify `FBSAgent._generate_matrix` to adjust transition probabilities:
      - Multiply off-diagonal elements by `resistant_speed_factor` (if `is_resistant`) and `velocity_modifier`. The remainder of the probability mass is added to the diagonal (stay probability).
    - Add `self.delay_steps: int = 0` to `FBSAgent`.
    - Modify `step(self, u)` to check `delay_steps`. If `> 0`, decrement and return `(False, False)` (no action).

3.  **Create `abm/scaling.py`**:
    - Implement `ScalingPenaltiesConfig` (Pydantic model) with default parameters from the paper: `coordination_rate = 0.3333`, `communication_barrier_rate = 0.3667`, etc.
    - Implement `ScalingPenalties` class to compute delays:
      - `get_waterfall_gate_delay(n_total_teams)`
      - `get_agile_sprint_review_delay(n_dependent_teams)`
      - `get_communication_delay()`

4.  **Update `abm/waterfall.py`**:
    - Accept an optional `ScalingPenalties` in `__init__`.
    - Maintain a `global_delay: int = 0`. If `> 0`, `step()` decrements it and returns.
    - When `current_phase` advances (a phase gate is reached), compute coordination delay and requirements cascade communication delay, adding them to `global_delay`.

5.  **Update `abm/agile.py`**:
    - Accept an optional `ScalingPenalties` and `velocity_modifier_type` (e.g., 'scrum', 'safe', 'kanban').
    - Maintain a per-team delay counter `team_delays: dict[int, int]`. If `team_delays[team_id] > 0`, the team's agents do not process `step()`.
    - When a team finishes a function (sprint review), compute sprint review coordination delay and add to that team's delay.
    - At every 24th time step (daily scrum), for each team, randomly draw a communication delay and add it to `team_delays`.
    - Randomly assign `is_resistant = True` to 20% of agents if `ScalingPenalties` is active.

6.  **Create `simulations/run_phase2.py`**:
    - Build a simulation orchestrator that sweeps `n_submodule_teams` over `[4, 8, 12, 20, 32, 50]`.
    - At each size, configure the appropriate number of agents and run both Agile and Waterfall with ScalingPenalties applied.
    - Measure and record `total_time` ratios (Agile/Waterfall).

7.  **Create `analysis/plots.py`**:
    - Implement function to plot the scaling curve: X-axis = `n_submodule_teams`, Y-axis = Agile Advantage (e.g., Waterfall Time / Agile Time).

8.  **Create `tests/test_scaling.py`**:
    - TDD approach: write unit tests for `ScalingPenalties` calculations.
    - Write integration tests checking that Agile efficiency drops as `n_teams` increases.

9.  **Pre-commit steps**:
    - Ensure proper testing, verification, review, and reflection are done (Ruff, Mypy, Pytest coverage >= 90%).

10. **Submit**:
    - Submit the changes using the provided tool.
