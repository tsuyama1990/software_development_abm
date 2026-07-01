"""Hybrid Simulation Module.

BLUEPRINT:
Data Flow:
- Initializes different configurations for the three Hybrid models using Pydantic models.
- Hybrid1Simulation, Hybrid2Simulation, Hybrid3Simulation will use these configurations.
- For Hybrid 1: The agents go through a Waterfall phase (R->F), then iterative Agile sprints
  (F->S), and finally a Waterfall phase (S->D).
- For Hybrid 2: Two independent groups of agents are created. One group runs Waterfall (R->D),
  the other runs Agile sprints (R->D). At the end, there's an integration step which might
  cause rework in the Waterfall group.
- For Hybrid 3: Agents go through timeboxed mini-Waterfall cycles (R->D) for subsets
  of functions, until all functions are complete.
- Outputs: `RunMetrics` object after completion for each simulation.

Module Boundaries:
- Inputs: Pydantic configs (`Hybrid1Config`, etc), list of `FBSAgent`s.
- Outputs: `RunMetrics` object.

Key Interfaces:
- `Hybrid1Config`, `Hybrid2Config`, `Hybrid3Config`: Data models for configuration.
- `Hybrid1Simulation`, etc: Simulation classes with `run() -> RunMetrics` methods.
"""

from collections import defaultdict

import numpy as np
from pydantic import BaseModel, ConfigDict

from abm.agent import FBSAgent
from abm.config import FBSState
from abm.metrics import RunMetrics
from abm.scaling import ScalingPenalties


class Hybrid1Config(BaseModel):
    """Configuration for Hybrid 1 Model."""

    model_config = ConfigDict(extra="forbid", strict=True)

    dummy: int = 0


class Hybrid2Config(BaseModel):
    """Configuration for Hybrid 2 Model."""

    model_config = ConfigDict(extra="forbid", strict=True)

    waterfall_fraction: float = 0.60
    agile_fraction: float = 0.40
    integration_coupling: float = 0.15


class Hybrid3Config(BaseModel):
    """Configuration for Hybrid 3 Model."""

    model_config = ConfigDict(extra="forbid", strict=True)

    cycle_length_hours_min: float = 320.0
    cycle_length_hours_max: float = 480.0


class Hybrid1Simulation:
    """Simulates Hybrid Model 1 (Sequential + Iterative phases)."""

    def __init__(
        self,
        agents: list[FBSAgent],
        config: Hybrid1Config,
        functions_per_team: int = 10,
        scaling_penalties: ScalingPenalties | None = None,
        gate_review_hours: float = 0.0,
        n_teams_baseline: int = 12,
    ) -> None:
        """Initialize the simulation."""
        self.agents = agents
        self.config = config
        self.functions_per_team = functions_per_team
        self.scaling_penalties = scaling_penalties
        self.gate_review_hours = gate_review_hours
        self.n_teams_baseline = n_teams_baseline

        self.time_step = 0
        self.effort_hours = 0.0
        self.rework_hours = 0.0

        # Phase 0 = Requirements (R->F, Waterfall)
        # Phase 1 = Design + Development (F->S, Agile sprints)
        # Phase 2 = Integration + Validation (S->D, Waterfall)
        self.current_phase = 0

        self.global_delay = 0.0

        # Group agents by sub_module_id for the agile phase
        self.teams: dict[int, list[FBSAgent]] = defaultdict(list)
        for a in self.agents:
            self.teams[a.sub_module_id].append(a)

        self.team_ids = {a.sub_module_id for a in self.agents}
        self.n_total_teams = len(self.team_ids)

        self.team_backlogs: dict[int, list[int]] = {
            t_id: list(range(self.functions_per_team)) for t_id in self.teams
        }

    def _update_phase(self) -> None:
        if not self.agents:
            return

        min_state = min(agent.current_state for agent in self.agents)

        # In Hybrid 1, phase transitions can go backwards if rework pulls min_state down.
        all_backlogs_empty = all(len(b) == 0 for b in self.team_backlogs.values())

        new_phase = 0
        if min_state >= FBSState.STRUCTURE and all_backlogs_empty:
            new_phase = 2
        elif min_state >= FBSState.FUNCTIONS:
            new_phase = 1

        if new_phase > self.current_phase and self.scaling_penalties:
            # Sync gate delays
            self.global_delay += self.scaling_penalties.get_coordination_delay(
                n_teams=self.n_total_teams,
                n_teams_baseline=self.n_teams_baseline,
                base_delay=self.gate_review_hours,
            )

        self.current_phase = new_phase

    def step(self) -> bool:
        """Execute one time step (1 hour)."""
        self._update_phase()

        if self.global_delay >= 1.0:
            self.global_delay -= 1.0
            self.time_step += 1
            return False

        is_done = all(a.current_state == FBSState.DOCUMENTATION for a in self.agents)
        if is_done:
            return True

        rng = np.random.default_rng()
        min_state = min(agent.current_state for agent in self.agents)

        for a in self.agents:
            u = rng.uniform(0, 1)

            if self.current_phase == 0:
                # Waterfall R->F
                if a.current_state == min_state:
                    self.effort_hours += 1.0
                    a.step(u)
            elif self.current_phase == 1:
                # Agile F->S
                team_id = a.sub_module_id
                if not self.team_backlogs[team_id]:
                    # This team is done with all functions, they can help fix things if they drop below S
                    if a.current_state < FBSState.STRUCTURE:
                        self.effort_hours += 1.0
                        a.step(u)
                    continue

                # Working on backlog, they advance up to STRUCTURE
                if a.current_state < FBSState.STRUCTURE:
                    self.effort_hours += 1.0
                    a.step(u)

            elif self.current_phase == 2:
                # Waterfall S->D
                if a.current_state == min_state:
                    self.effort_hours += 1.0
                    a.step(u)

        if self.current_phase == 1:
            # Handle team completions for agile sprint
            for team_id, team in self.teams.items():
                if not self.team_backlogs[team_id]:
                    continue
                team_done = all(a.current_state >= FBSState.STRUCTURE for a in team)
                if team_done:
                    self.team_backlogs[team_id].pop(0)
                    if self.team_backlogs[team_id]:
                        for a in team:
                            a.current_state = FBSState.FUNCTIONS

        self.time_step += 1
        self._update_phase()

        return all(a.current_state == FBSState.DOCUMENTATION for a in self.agents)

    def run(self) -> RunMetrics:
        """Run the simulation to completion."""
        agent_max_states = {a.agent_id: a.current_state for a in self.agents}

        if not self.agents:
            return RunMetrics(total_time=0.0, effort_hours=0.0, rework_time=0.0)

        while not self.step():
            min_state = min(agent.current_state for agent in self.agents)
            for a in self.agents:
                agent_max_states[a.agent_id] = max(
                    agent_max_states[a.agent_id], a.current_state,
                )

                # Rework tracking based on if they were active this step
                active = False
                if (self.current_phase == 0 and a.current_state == min_state) or (self.current_phase == 1 and a.current_state < FBSState.STRUCTURE) or (self.current_phase == 2 and a.current_state == min_state):
                    active = True

                if active and a.current_state < agent_max_states[a.agent_id]:
                    self.rework_hours += 1.0

        return RunMetrics(
            total_time=float(self.time_step),
            effort_hours=self.effort_hours,
            rework_time=self.rework_hours,
        )


class Hybrid2Simulation:
    """Simulates Hybrid Model 2 (Parallel Sub-Projects)."""

    def __init__(
        self,
        agents: list[FBSAgent],
        config: Hybrid2Config,
        functions_per_team: int = 10,
        scaling_penalties: ScalingPenalties | None = None,
        gate_review_hours: float = 0.0,
        inter_team_meeting_hours: float = 0.0,
        n_teams_baseline: int = 12,
    ) -> None:
        """Initialize the simulation."""
        self.agents = agents
        self.config = config
        self.functions_per_team = functions_per_team
        self.scaling_penalties = scaling_penalties

        self.time_step = 0
        self.effort_hours = 0.0
        self.rework_hours = 0.0

        if not self.agents:
            self.waterfall_agents: list[FBSAgent] = []
            self.agile_agents: list[FBSAgent] = []
            self.agile_teams: dict[int, list[FBSAgent]] = {}
            self.agile_backlogs: dict[int, list[int]] = {}
            return

        # Split agents based on config fraction
        split_idx = int(len(self.agents) * self.config.waterfall_fraction)
        # Ensure at least 1 agent in each group if there are at least 2 agents
        if split_idx == 0 and len(self.agents) > 1:
            split_idx = 1
        elif split_idx == len(self.agents) and len(self.agents) > 1:
            split_idx = len(self.agents) - 1

        self.waterfall_agents = self.agents[:split_idx]
        self.agile_agents = self.agents[split_idx:]

        # Setup waterfall
        self.w_current_phase = 0
        self.w_global_delay = 0.0
        self.w_team_ids = {a.sub_module_id for a in self.waterfall_agents}
        self.w_n_teams = len(self.w_team_ids)
        self.w_gate_review_hours = gate_review_hours
        self.w_n_teams_baseline = n_teams_baseline

        # Setup agile
        self.agile_teams = defaultdict(list)
        for a in self.agile_agents:
            self.agile_teams[a.sub_module_id].append(a)

        self.agile_backlogs = {
            t_id: list(range(self.functions_per_team)) for t_id in self.agile_teams
        }
        self.a_delays: dict[int, float] = defaultdict(float)
        self.a_inter_team_meeting_hours = inter_team_meeting_hours
        self.a_n_teams_baseline = n_teams_baseline

        self.agile_integrated = False
        if not self.agile_agents:
            self.agile_integrated = True

    def _update_waterfall_phase(self) -> None:
        if not self.waterfall_agents:
            return

        min_state = min(a.current_state for a in self.waterfall_agents)
        new_phase = int(min_state)

        if new_phase > self.w_current_phase and self.scaling_penalties:
            self.w_global_delay += self.scaling_penalties.get_coordination_delay(
                n_teams=self.w_n_teams,
                n_teams_baseline=self.w_n_teams_baseline,
                base_delay=self.w_gate_review_hours,
            )

        self.w_current_phase = new_phase

    def step(self) -> bool:
        """Execute one time step."""
        rng = np.random.default_rng()

        # Step Waterfall group
        w_done = True
        if self.waterfall_agents:
            self._update_waterfall_phase()

            if self.w_global_delay >= 1.0:
                self.w_global_delay -= 1.0
                w_done = False
            else:
                w_done = all(a.current_state == FBSState.DOCUMENTATION for a in self.waterfall_agents)
                if not w_done:
                    for a in self.waterfall_agents:
                        if a.current_state == self.w_current_phase:
                            # We record that they worked for rework tallying
                            a._worked_this_step = True
                            self.effort_hours += 1.0
                            a.step(rng.uniform(0, 1))
                        else:
                            a._worked_this_step = False

        # Step Agile group
        a_done = True
        if self.agile_agents:
            a_done = all(len(b) == 0 for b in self.agile_backlogs.values())
            if not a_done:
                for team_id, team in self.agile_teams.items():
                    if not self.agile_backlogs[team_id]:
                        continue

                    if self.a_delays[team_id] >= 1.0:
                        self.a_delays[team_id] -= 1.0
                        continue

                    for a in team:
                        if a.current_state != FBSState.DOCUMENTATION:
                            self.effort_hours += 1.0
                            a.step(rng.uniform(0, 1))

                    team_done = all(a.current_state == FBSState.DOCUMENTATION for a in team)
                    if team_done:
                        self.agile_backlogs[team_id].pop(0)
                        if self.scaling_penalties:
                            # Agile team integration delay
                            self.a_delays[team_id] += self.scaling_penalties.get_coordination_delay(
                                n_teams=1, # simplified
                                n_teams_baseline=self.a_n_teams_baseline,
                                base_delay=self.a_inter_team_meeting_hours,
                            )

                        if self.agile_backlogs[team_id]:
                            for a in team:
                                a.current_state = FBSState.REQUIREMENTS

        # Integration event: when Agile completes, it might trigger rework in Waterfall
        if a_done and not self.agile_integrated and self.waterfall_agents:
            self.agile_integrated = True

            # Integration coupling rework trigger
            if rng.random() < self.config.integration_coupling:
                for a in self.waterfall_agents:
                    # Drop to EXPECTED_BEHAVIOR (Type I reformulation) if they are past it
                    a.current_state = min(a.current_state, FBSState.EXPECTED_BEHAVIOR)

            # Need to update waterfall phase since we might have dropped states
            self._update_waterfall_phase()

            # Note: We must re-evaluate w_done since we might have just knocked them out of state D
            w_done = all(a.current_state == FBSState.DOCUMENTATION for a in self.waterfall_agents)

        self.time_step += 1
        return w_done and a_done

    def run(self) -> RunMetrics:
        """Run simulation to completion."""
        if not self.agents:
            return RunMetrics(total_time=0.0, effort_hours=0.0, rework_time=0.0)

        return self._run_with_accurate_rework()

    def _run_with_accurate_rework(self) -> RunMetrics:
        """Run simulation to completion with accurate rework counting."""
        w_max_states = {a.agent_id: a.current_state for a in self.waterfall_agents}
        a_max_states = {a.agent_id: a.current_state for a in self.agile_agents}

        while True:
            # Check pre-step states to see who is going to work and if it's rework
            for a in self.waterfall_agents:
                if a.current_state == self.w_current_phase and a.current_state < w_max_states[a.agent_id]:
                    self.rework_hours += 1.0

            for a in self.agile_agents:
                # Only check agile rework if they are active (not DOCUMENTATION)
                if a.current_state != FBSState.DOCUMENTATION and a.current_state < a_max_states[a.agent_id]:
                    self.rework_hours += 1.0

            done = self.step()

            for a in self.waterfall_agents:
                w_max_states[a.agent_id] = max(w_max_states[a.agent_id], a.current_state)

            for a in self.agile_agents:
                # reset max state if they went back to requirements
                if a.current_state == FBSState.REQUIREMENTS:
                    a_max_states[a.agent_id] = FBSState.REQUIREMENTS
                else:
                    a_max_states[a.agent_id] = max(a_max_states[a.agent_id], a.current_state)

            if done:
                break

        return RunMetrics(
            total_time=float(self.time_step),
            effort_hours=self.effort_hours,
            rework_time=self.rework_hours,
        )


class Hybrid3Simulation:
    """Simulates Hybrid Model 3 (Mini Traditional Cycles)."""

    def __init__(
        self,
        agents: list[FBSAgent],
        config: Hybrid3Config,
        total_functions: int = 120,
        scaling_penalties: ScalingPenalties | None = None,
        gate_review_hours: float = 0.0,
        n_teams_baseline: int = 12,
    ) -> None:
        """Initialize the simulation."""
        self.agents = agents
        self.config = config
        self.scaling_penalties = scaling_penalties

        self.time_step = 0
        self.effort_hours = 0.0
        self.rework_hours = 0.0

        self.total_functions = total_functions
        self.completed_functions = 0

        self.gate_review_hours = gate_review_hours
        self.n_teams_baseline = n_teams_baseline
        self.global_delay = 0.0

        if self.agents:
            self.team_ids = {a.sub_module_id for a in self.agents}
            self.n_total_teams = len(self.team_ids)
        else:
            self.n_total_teams = 0

        self._start_new_cycle()

    def _start_new_cycle(self) -> None:
        """Initialize a new timeboxed cycle."""
        rng = np.random.default_rng()
        self.cycle_time = 0
        self.cycle_limit = rng.uniform(
            self.config.cycle_length_hours_min,
            self.config.cycle_length_hours_max,
        )

        self.cycle_phase = 0
        for a in self.agents:
            a.current_state = FBSState.REQUIREMENTS

        # Estimate how many functions we can do based on remaining and limit
        # For simplicity in ABM, we just assume the agents work on a "batch" of functions during this cycle.
        # When the cycle ends, whatever progress they made contributes to the total.
        # Or more accurately, if they hit state D, they complete a batch.
        # Let's say a batch is max 10 functions.
        self.current_batch_size = min(10, self.total_functions - self.completed_functions)

    def _update_phase(self) -> None:
        if not self.agents:
            return

        min_state = min(a.current_state for a in self.agents)
        new_phase = int(min_state)

        if new_phase > self.cycle_phase and self.scaling_penalties:
            self.global_delay += self.scaling_penalties.get_coordination_delay(
                n_teams=self.n_total_teams,
                n_teams_baseline=self.n_teams_baseline,
                base_delay=self.gate_review_hours,
            )

        self.cycle_phase = new_phase

    def step(self) -> bool:
        """Execute one time step."""
        if not self.agents:
            self.completed_functions = self.total_functions
            return True

        self._update_phase()

        if self.global_delay >= 1.0:
            self.global_delay -= 1.0
            self.time_step += 1
            self.cycle_time += 1
            return False

        rng = np.random.default_rng()

        all_d = all(a.current_state == FBSState.DOCUMENTATION for a in self.agents)
        if not all_d:
            for a in self.agents:
                if a.current_state == self.cycle_phase:
                    self.effort_hours += 1.0
                    a.step(rng.uniform(0, 1))

        self.time_step += 1
        self.cycle_time += 1

        # Check if cycle ends (timebox reached or all done)
        if all_d or self.cycle_time >= self.cycle_limit:
            if all_d:
                # Batch completed successfully
                self.completed_functions += self.current_batch_size
            else:
                # Timebox reached before completion. Progress is lost/rolled back (rework overhead).
                # Only a fraction might be completed, or zero. We'll say zero for strict timeboxing.
                pass

            if self.completed_functions < self.total_functions:
                self._start_new_cycle()

        return self.completed_functions >= self.total_functions

    def run(self) -> RunMetrics:
        """Run the simulation to completion."""
        if not self.agents:
            return RunMetrics(total_time=0.0, effort_hours=0.0, rework_time=0.0)

        max_states = {a.agent_id: a.current_state for a in self.agents}

        while not self.step():
            # Tally rework within the cycle
            for a in self.agents:
                # Rework is when state drops within a cycle
                if a.current_state == self.cycle_phase and a.current_state < max_states[a.agent_id]:
                    self.rework_hours += 1.0

            for a in self.agents:
                # Reset max_states if a new cycle just started (indicated by being at R while previous was higher)
                # Actually _start_new_cycle resets everyone to R
                if a.current_state == FBSState.REQUIREMENTS and max_states[a.agent_id] > FBSState.REQUIREMENTS:
                    max_states[a.agent_id] = FBSState.REQUIREMENTS
                else:
                    max_states[a.agent_id] = max(max_states[a.agent_id], a.current_state)

        return RunMetrics(
            total_time=float(self.time_step),
            effort_hours=self.effort_hours,
            rework_time=self.rework_hours,
        )
