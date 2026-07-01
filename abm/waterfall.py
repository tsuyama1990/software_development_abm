"""Waterfall Simulation Module.

BLUEPRINT:
Data Flow:
- Initializes a list of FBSAgents representing the software team.
- Iterates time steps.
- In each step, evaluates the global phase (determined by the minimum state of all agents).
- Agents only attempt a transition if their current state is <= the global phase.
- If an agent reworks to a previous state, it forces the global phase to drop back,
  making other agents wait (synchronization).
- Stops when all agents reach the DOCUMENTATION (absorbing) state.

Module Boundaries:
- Inputs: List of `FBSAgent` objects.
- Outputs: `RunMetrics` object after completion.

Key Interfaces:
- `WaterfallSimulation(agents: list[FBSAgent])`
- `WaterfallSimulation.run() -> RunMetrics`
- `WaterfallSimulation.step()`
"""

import numpy as np

from abm.agent import FBSAgent
from abm.config import FBSState
from abm.metrics import RunMetrics
from abm.scaling import ScalingPenalties


class WaterfallSimulation:
    """Simulates a software project using the Waterfall methodology.

    Features global phase synchronization gates (SRR, SFR, PDR, CDR).
    """

    def __init__(
        self,
        agents: list[FBSAgent],
        scaling_penalties: ScalingPenalties | None = None,
        gate_review_hours: float = 0.0,
        cascade_low_delay: float = 0.0,
        cascade_high_delay: float = 0.0,
        n_teams_baseline: int = 12,
    ) -> None:
        """Initialize the simulation with a list of agents."""
        self.agents = agents
        self.time_step = 0
        self.effort_hours = 0.0
        self.rework_hours = 0.0

        # Phase 2 delays
        self.scaling_penalties = scaling_penalties
        self.gate_review_hours = gate_review_hours
        self.cascade_low_delay = cascade_low_delay
        self.cascade_high_delay = cascade_high_delay
        self.n_teams_baseline = n_teams_baseline
        self.global_delay = 0.0

        # Teams involved for scaling calculations
        self.team_ids = {a.sub_module_id for a in self.agents}
        self.n_total_teams = len(self.team_ids)

        # The current phase is defined by the minimum state of any agent.
        # Phase 0 = Requirements (R->F)
        # Phase 1 = Functions (F->Be)
        # Phase 2 = Expected Behavior (Be->S)
        # Phase 3 = Structure (S->D)
        # Phase 4 = Documentation (Done)
        self.current_phase = 0

    def _update_phase(self) -> None:
        """Update the global phase based on the slowest agent."""
        if not self.agents:
            return  # pragma: no cover

        min_state = min(agent.current_state for agent in self.agents)
        new_phase = int(min_state)

        # Phase has advanced (sync gate reached)
        if new_phase > self.current_phase and self.scaling_penalties:
            # Add coordination delay for the sync gate
            self.global_delay += self.scaling_penalties.get_coordination_delay(
                n_teams=self.n_total_teams,
                n_teams_baseline=self.n_teams_baseline,
                base_delay=self.gate_review_hours,
            )
            # Add communication delay for the cascade
            self.global_delay += self.scaling_penalties.get_communication_delay(
                low_delay=self.cascade_low_delay,
                high_delay=self.cascade_high_delay,
            )

        self.current_phase = new_phase

    def step(self) -> bool:
        """Execute one time step (1 hour) of the simulation.

        Returns:
            bool: True if the simulation is complete (all agents in state D), False otherwise.

        """
        self._update_phase()

        if self.global_delay >= 1.0:
            self.global_delay -= 1.0
            self.time_step += 1
            return False

        if self.current_phase == int(FBSState.DOCUMENTATION):
            return True # All done

        rng = np.random.default_rng()

        for agent in self.agents:
            # An agent only works if it hasn't finished the current global phase.
            # If agent.current_state > self.current_phase, it's waiting for others.
            if agent.current_state == self.current_phase:
                u = rng.uniform(0, 1)

                # effort is expended when an agent is working
                self.effort_hours += 1.0

                _advanced, _reworked = agent.step(u)

                # Rework accounting is handled globally in the `run` loop based on max states.

        self.time_step += 1
        self._update_phase()

        return self.current_phase == int(FBSState.DOCUMENTATION)

    def run(self) -> RunMetrics:
        """Run the simulation to completion.

        Returns:
            RunMetrics: Metrics for this simulation run.

        """
        # We need a robust way to track rework time.
        # Rework time is defined as time spent on tasks triggered by reformulations.
        # We can track the maximum state reached by each agent.
        # If an agent is working in a state lower than its max reached state, it's doing rework.

        agent_max_states = {agent.agent_id: agent.current_state for agent in self.agents}

        # Prevent infinite loop if no agents
        if not self.agents:
            return RunMetrics(total_time=0.0, effort_hours=0.0, rework_time=0.0)

        while not self.step():
            # The step() method increments self.effort_hours for every agent that acts.
            # Here, let's tally rework_hours.
            for agent in self.agents:
                # Update max state seen
                agent_max_states[agent.agent_id] = max(
                    agent_max_states[agent.agent_id], agent.current_state,
                )

                # If they are working (their state == current_phase) and their state is
                # less than max seen, they are re-doing work.
                if (
                    agent.current_state == self.current_phase
                    and agent.current_state < agent_max_states[agent.agent_id]
                ):
                    self.rework_hours += 1.0

        return RunMetrics(
            total_time=float(self.time_step),
            effort_hours=self.effort_hours,
            rework_time=self.rework_hours,
        )
