1.  **Create `abm/scaling.py`**:
    - Add `ScalingPenaltiesConfig` (Pydantic model) to hold configuration for coordination, communication, and resistance based on the roadmap.
    - Add `ScalingPenalties` class to calculate coordination delays and communication delays according to the equations in the roadmap.
    - Verify with `cat abm/scaling.py`.

2.  **Update `abm/config.py` and `abm/agent.py`**:
    - `abm/config.py`: Add properties for resistance and velocity to `AgentConfig`.
    - `abm/agent.py`: Update transition probability generation to scale probabilities based on resistance and velocity modifiers. Add a delay property to skip steps when active.
    - Verify with `cat abm/agent.py` and `cat abm/config.py`.

3.  **Update `abm/waterfall.py`**:
    - Update constructor to accept scaling penalties and required delay parameters as configurable arguments.
    - Add a global delay tracker.
    - When transitioning between phases, compute and add coordination and communication delays to the global delay tracker.
    - Verify with `cat abm/waterfall.py`.

4.  **Update `abm/agile.py`**:
    - Update constructor to accept scaling penalties and required delay parameters as configurable arguments.
    - Add a team-level delay tracker.
    - During sprints, apply communication delays. When functions complete, calculate and add sprint review coordination delays to the team's tracker.
    - Set a portion of agents to be resistant based on the roadmap.
    - Verify with `cat abm/agile.py`.

5.  **Create `simulations/run_phase2.py`**:
    - Implement a sweep loop over team sizes as specified in the issue (4 to 50 teams).
    - Construct the proper number of agents.
    - Apply the Phase 2 simulation classes for Agile and Waterfall passing the `ScalingPenalties` config.
    - Pass necessary configurations as variables without hardcoding assumed defaults.
    - Run Monte Carlo simulations and collect metrics. Output the results.
    - Verify with `cat simulations/run_phase2.py`.

6.  **Update `analysis/plots.py`**:
    - Add a function to plot the scaling curve of team sizes versus Agile advantage.
    - Verify with `cat analysis/plots.py`.

7.  **Create tests in `tests/test_scaling.py`**:
    - Implement unit tests for coordination and communication delay calculations.
    - Implement an integration test running `AgileSimulation` with and without scaling penalties to verify delays increase completion time.
    - Verify with `cat tests/test_scaling.py`.

8.  **Verify and Test**:
    - Run `pytest --cov --cov-branch --cov-fail-under=90`
    - Run `ruff check --select ALL` and `mypy --strict`

9.  **Complete Pre-commit Steps**:
    - Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done.

10. **Submit Change**:
    - Call the `submit` tool to finalize work.
