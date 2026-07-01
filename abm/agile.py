"""
Agile Simulation Module.

BLUEPRINT:
Data Flow:
- Initializes planning agents (leads) and team agents (sub-module designers).
- Phase A (Planning): Leads traverse R->F representing backlog generation.
- Phase B (Sprints):
  - Teams pull from their backlog of functions.
  - Teams execute the full FBS cycle (R->D) for each function in parallel.
  - No cross-team synchronization.
  - If an agent triggers a reformulation (rework), they step backwards.
    (For this simplified ABM, it just means they take more steps to finish).

Module Boundaries:
- Inputs: List of lead `FBSAgent`s, list of team `FBSAgent`s, functions per team.
- Outputs: `RunMetrics` object.

Key Interfaces:
- `AgileSimulation(leads: list[FBSAgent], agents: list[FBSAgent], functions_per_team: int)`
- `AgileSimulation.run() -> RunMetrics`
"""

from collections import defaultdict

import numpy as np

from abm.agent import FBSAgent
from abm.config import FBSState
from abm.metrics import RunMetrics
from abm.scaling import ScalingPenalties


class AgileSimulation:
    """
    Simulates a software project using the Agile methodology.

    Features an initial planning phase and parallel, unsynchronized sprints.
    """

    def __init__(
        self,
        leads: list[FBSAgent],
        agents: list[FBSAgent],
        functions_per_team: int = 10,
        scaling_penalties: ScalingPenalties | None = None,
        inter_team_meeting_hours: float = 0.0,
        scrum_low_delay: float = 0.0,
        scrum_high_delay: float = 0.0,
        scrum_velocity_modifier: float = 1.0,
        daily_scrum_interval: int = 24,
        n_teams_baseline: int = 12,
    ) -> None:
        """Initialize with program/module leads and sub-module agents."""
        self.leads = leads
        self.agents = agents
        self.functions_per_team = functions_per_team

        # Scaling parameters
        self.scaling_penalties = scaling_penalties
        self.inter_team_meeting_hours = inter_team_meeting_hours
        self.scrum_low_delay = scrum_low_delay
        self.scrum_high_delay = scrum_high_delay
        self.scrum_velocity_modifier = scrum_velocity_modifier
        self.daily_scrum_interval = daily_scrum_interval
        self.n_teams_baseline = n_teams_baseline

        self.team_delays: dict[int, float] = defaultdict(float)

        # Group agents by sub_module_id
        self.teams: dict[int, list[FBSAgent]] = defaultdict(list)
        for a in self.agents:
            self.teams[a.sub_module_id].append(a)

        if not self.agents and not self.leads:
            self.planning_complete = True

        self.team_backlogs: dict[int, list[int]] = {
            t_id: list(range(functions_per_team)) for t_id in self.teams
        }

        self.time_step = 0
        self.effort_hours = 0.0
        self.rework_hours = 0.0

        self.planning_complete = False

    def _run_planning_phase(self) -> None:
        """Phase A: Leads define the backlog (R->F)."""
        if not self.leads:
            self.planning_complete = True
            return

        rng = np.random.default_rng()

        while True:
            all_done = True
            for lead in self.leads:
                if lead.current_state < FBSState.FUNCTIONS:
                    all_done = False
                    u = rng.uniform(0, 1)
                    self.effort_hours += 1.0
                    _adv, _rew = lead.step(u)

            if all_done:
                break

            self.time_step += 1

        self.planning_complete = True

    def _apply_daily_scrum_delays(self) -> None:
        if (self.scaling_penalties and self.daily_scrum_interval > 0 and
            self.time_step > 0 and self.time_step % self.daily_scrum_interval == 0):
            for team_id in self.teams:
                delay = self.scaling_penalties.get_communication_delay(
                    self.scrum_low_delay, self.scrum_high_delay,
                )
                self.team_delays[team_id] += delay

    def _handle_team_done(self, team_id: int, team: list[FBSAgent]) -> None:
        self.team_backlogs[team_id].pop(0)

        if self.scaling_penalties:
            # Calculate coordination cost for sprint review
            module_id = team[0].module_id
            n_dependent_teams = sum(
                1 for t in self.teams.values() if t and t[0].module_id == module_id
            )

            delay = self.scaling_penalties.get_coordination_delay(
                n_teams=n_dependent_teams,
                n_teams_baseline=self.n_teams_baseline,
                base_delay=self.inter_team_meeting_hours,
            )
            self.team_delays[team_id] += delay

        if self.team_backlogs[team_id]:
            for a in team:
                a.current_state = FBSState.REQUIREMENTS

    def step(self) -> None:
        """Execute one time step (1 hour) of the parallel sprints."""
        rng = np.random.default_rng()

        self._apply_daily_scrum_delays()

        for team_id, team in self.teams.items():
            if not self.team_backlogs[team_id]:
                continue # Team is done with all its functions

            if self.team_delays[team_id] >= 1.0:
                self.team_delays[team_id] -= 1.0
                continue

            # Team members work on the current function
            for a in team:
                if a.current_state != FBSState.DOCUMENTATION:
                    u = rng.uniform(0, 1)
                    self.effort_hours += 1.0

                    _adv, _rew = a.step(u)

            # Check if team completed a function
            team_done = all(a.current_state == FBSState.DOCUMENTATION for a in team)
            if team_done:
                self._handle_team_done(team_id, team)

        self.time_step += 1

    def is_complete(self) -> bool:
        """Check if all teams have emptied their backlogs."""
        return all(len(backlog) == 0 for backlog in self.team_backlogs.values())

    def get_metrics(self) -> RunMetrics:
        """Return the current metrics."""
        return RunMetrics(
            total_time=float(self.time_step),
            effort_hours=self.effort_hours,
            rework_time=self.rework_hours,
        )

    def run(self) -> RunMetrics:
        """Run the simulation to completion."""
        if not self.planning_complete:
            self._run_planning_phase()

        # Track max state per agent to measure rework
        # (agent_id -> max_state)
        agent_max_states = {}
        for a in self.agents:
            agent_max_states[a.agent_id] = a.current_state

        while not self.is_complete():
            pre_states = {a.agent_id: a.current_state for a in self.agents}

            self.step()

            for team in self.teams.values():
                for a in team:
                    # If they started a new function
                    if (
                        pre_states[a.agent_id] == FBSState.DOCUMENTATION
                        and a.current_state == FBSState.REQUIREMENTS
                    ):
                        agent_max_states[a.agent_id] = FBSState.REQUIREMENTS

                    agent_max_states[a.agent_id] = max(
                        agent_max_states[a.agent_id], a.current_state,
                    )

                    # Check if they were active
                    if (
                        pre_states[a.agent_id] != FBSState.DOCUMENTATION
                        and a.current_state < agent_max_states[a.agent_id]
                    ):
                        self.rework_hours += 1.0

        return self.get_metrics()
