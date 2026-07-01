"""Configuration and state definitions for the software development ABM.

This module provides the central state enumerations and calibrated matrices
for the FBS (Function-Behavior-Structure) Markov agents, as described by
Bott & Mesmer (2019).
"""

from enum import Enum, IntEnum
from typing import ClassVar

from pydantic import BaseModel, ConfigDict


class AIMode(str, Enum):
    """Modes for AI assistance in the software development process."""

    NO_AI = "no_ai"
    AI_RAW = "ai_raw"
    AI_REACT = "ai_react"


# AI Modifiers
AI_SPEED = 4.0
AI_REWORK = 3.0
REACT_REWORK = 1.2

# Sensitivity analysis ranges
AI_SPEED_RANGE = (3.0, 5.0)
AI_REWORK_RANGE = (2.0, 4.0)
REACT_REWORK_RANGE = (1.1, 1.3)


class FBSState(IntEnum):
    """The 5 states in the collapsed FBS model."""

    REQUIREMENTS = 0  # R
    FUNCTIONS = 1  # F
    EXPECTED_BEHAVIOR = 2  # Be / Bs
    STRUCTURE = 3  # S
    DOCUMENTATION = 4  # D (Absorbing)


class BaseTransitionMatrix:
    """Calibrated base transition matrices for the 5-state Markov chain.

    Rows and columns correspond to FBSState (0..4).

    States: R=0, F=1, Be=2, S=3, D=4
    Transitions mechanics per time step:
    - Draw random float u ~ Uniform(0, 1)
    - If u > probability: advance to next state
    - If u <= probability: stay in current state (working)

    Rework:
    - Type III: jump back to R
    - Type I/II: jump back to Be
    """

    # These are initial notional values tuned to match the 5% validation bounds
    # from the Bott & Mesmer (2019) paper for uncoupled software development.

    # Mean transition probabilities (agent i = mean + rand() * (high - mean))
    MEAN: ClassVar[list[list[float]]] = [
        [0.90, 0.10, 0.00, 0.00, 0.00],  # R
        [0.05, 0.15, 0.80, 0.00, 0.00],  # F (F->R rework = 0.05)
        [0.00, 0.00, 0.50, 0.50, 0.00],  # Be
        [0.02, 0.00, 0.08, 0.50, 0.40],  # S (S->R rework = 0.02, S->Be rework = 0.08)
        [0.00, 0.00, 0.00, 0.00, 1.00],  # D (absorbing)
    ]

    # High side of 90% confidence interval
    HIGH: ClassVar[list[list[float]]] = [
        [0.95, 0.05, 0.00, 0.00, 0.00],  # R
        [0.02, 0.08, 0.90, 0.00, 0.00],  # F
        [0.00, 0.00, 0.40, 0.60, 0.00],  # Be
        [0.01, 0.00, 0.04, 0.40, 0.55],  # S
        [0.00, 0.00, 0.00, 0.00, 1.00],  # D
    ]


class AgentConfig(BaseModel):
    """Configuration for an FBS Agent."""

    model_config = ConfigDict(extra="forbid", strict=True)

    agent_id: int
    module_id: int
    sub_module_id: int
    mean_matrix: list[list[float]] = BaseTransitionMatrix.MEAN
    high_matrix: list[list[float]] = BaseTransitionMatrix.HIGH
    is_resistant: bool = False
    resistant_speed_factor: float = 1.0
    velocity_modifier: float = 1.0
    ai_mode: AIMode = AIMode.NO_AI
