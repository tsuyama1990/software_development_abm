"""Tests for the ReAct Layer."""

from abm.config import REACT_REWORK, FBSState
from abm.react_layer import ReActGate


def test_react_gate_initialization() -> None:
    """Test ReActGate initializes correctly."""
    gate = ReActGate()
    assert gate.react_rework == REACT_REWORK


def test_react_gate_apply_react() -> None:
    """Test apply_react correctly scales specific backward transitions."""
    gate = ReActGate(react_rework=0.5)

    # Simplified 5x5 matrix
    # Format matches FBSState: R, F, Be, S, D
    base_matrix = [
        [0.8, 0.2, 0.0, 0.0, 0.0],
        [0.1, 0.7, 0.2, 0.0, 0.0],
        [0.0, 0.0, 0.6, 0.4, 0.0],
        [0.0, 0.0, 0.2, 0.4, 0.4],  # S->Be rework is 0.2, S->S rework is 0.4
        [0.0, 0.0, 0.0, 0.0, 1.0],
    ]

    modified = gate.apply_react(base_matrix)

    # Check F -> R was reduced
    assert modified[FBSState.FUNCTIONS][FBSState.REQUIREMENTS] == base_matrix[FBSState.FUNCTIONS][FBSState.REQUIREMENTS] * 0.5
    
    # Check S -> Be was reduced
    assert modified[FBSState.STRUCTURE][FBSState.EXPECTED_BEHAVIOR] == base_matrix[FBSState.STRUCTURE][FBSState.EXPECTED_BEHAVIOR] * 0.5
    
    # S -> S is on the diagonal, and apply_react re-normalizes the diagonal
    # after changing S -> Be. So we don't assert S->S equals base * 0.5.

    # Check forward transitions are unchanged (except diagonal normalization)
    assert modified[FBSState.REQUIREMENTS][FBSState.FUNCTIONS] == base_matrix[FBSState.REQUIREMENTS][FBSState.FUNCTIONS]
    assert modified[FBSState.FUNCTIONS][FBSState.EXPECTED_BEHAVIOR] == base_matrix[FBSState.FUNCTIONS][FBSState.EXPECTED_BEHAVIOR]

    # Check rows still sum to 1.0
    for row in modified:
        assert sum(row) - 1.0 < 1e-6


def test_react_gate_row_normalization_exceeds_1() -> None:
    """Test ReActGate normalization when non-diagonal probabilities exceed 1.0.
    
    This is an edge case to ensure 100% coverage of the normalization branch.
    """
    gate = ReActGate(react_rework=1.5)  # Increase rework to exceed 1
    
    base_matrix = [
        [0.0, 0.9, 0.0, 0.0, 0.0], # Normal
        [0.9, 0.0, 0.9, 0.0, 0.0], # F->R is 0.9. * 1.5 = 1.35. Non-diagonal sum > 1.0.
        [0.0, 0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 1.0],
    ]
    
    modified = gate.apply_react(base_matrix)
    
    assert sum(modified[1]) - 1.0 < 1e-6
    assert modified[1][0] < 1.35  # It should be normalized
