"""Tests for the AI Layer."""

from abm.ai_layer import apply_ai_modifiers
from abm.config import AI_REWORK, AI_SPEED, AIMode, FBSState


def test_apply_ai_modifiers_no_ai() -> None:
    """Test NO_AI mode returns unchanged matrix."""
    base_matrix = [
        [0.8, 0.2, 0.0, 0.0, 0.0],
        [0.1, 0.7, 0.2, 0.0, 0.0],
        [0.0, 0.0, 0.6, 0.4, 0.0],
        [0.0, 0.0, 0.2, 0.4, 0.4],
        [0.0, 0.0, 0.0, 0.0, 1.0],
    ]
    
    modified = apply_ai_modifiers(base_matrix, AIMode.NO_AI)
    assert modified == base_matrix


def test_apply_ai_modifiers_ai_raw() -> None:
    """Test AI_RAW mode applies speed and high rework."""
    base_matrix = [
        [0.8, 0.1, 0.0, 0.0, 0.0],
        [0.1, 0.8, 0.1, 0.0, 0.0],
        [0.0, 0.0, 0.9, 0.1, 0.0],
        [0.0, 0.0, 0.1, 0.8, 0.1],
        [0.0, 0.0, 0.0, 0.0, 1.0],
    ]
    
    modified = apply_ai_modifiers(base_matrix, AIMode.AI_RAW)
    
    # Check speed boost applied to forward transitions
    assert modified[FBSState.REQUIREMENTS][FBSState.FUNCTIONS] == base_matrix[FBSState.REQUIREMENTS][FBSState.FUNCTIONS] * AI_SPEED
    assert modified[FBSState.FUNCTIONS][FBSState.EXPECTED_BEHAVIOR] == base_matrix[FBSState.FUNCTIONS][FBSState.EXPECTED_BEHAVIOR] * AI_SPEED
    assert modified[FBSState.EXPECTED_BEHAVIOR][FBSState.STRUCTURE] == base_matrix[FBSState.EXPECTED_BEHAVIOR][FBSState.STRUCTURE] * AI_SPEED
    assert modified[FBSState.STRUCTURE][FBSState.DOCUMENTATION] == base_matrix[FBSState.STRUCTURE][FBSState.DOCUMENTATION] * AI_SPEED
    
    # Check rework penalty applied to backward transitions
    assert modified[FBSState.FUNCTIONS][FBSState.REQUIREMENTS] == base_matrix[FBSState.FUNCTIONS][FBSState.REQUIREMENTS] * AI_REWORK
    assert modified[FBSState.STRUCTURE][FBSState.EXPECTED_BEHAVIOR] == base_matrix[FBSState.STRUCTURE][FBSState.EXPECTED_BEHAVIOR] * AI_REWORK
    # S -> S is updated via diagonal normalization in apply_ai_modifiers
    # so we shouldn't directly assert it equals base_matrix * AI_REWORK

    # Check rows sum to 1.0
    for row in modified:
        assert sum(row) - 1.0 < 1e-6


def test_apply_ai_modifiers_ai_react() -> None:
    """Test AI_REACT mode applies speed and mitigated rework."""
    base_matrix = [
        [0.8, 0.1, 0.0, 0.0, 0.0],
        [0.1, 0.8, 0.1, 0.0, 0.0],
        [0.0, 0.0, 0.9, 0.1, 0.0],
        [0.0, 0.0, 0.1, 0.8, 0.1],
        [0.0, 0.0, 0.0, 0.0, 1.0],
    ]
    
    modified = apply_ai_modifiers(base_matrix, AIMode.AI_REACT)
    
    # Check speed boost applied
    assert modified[FBSState.REQUIREMENTS][FBSState.FUNCTIONS] == base_matrix[FBSState.REQUIREMENTS][FBSState.FUNCTIONS] * AI_SPEED
    
    # Rework should be mitigated by ReAct (not using AI_REWORK)
    assert modified[FBSState.FUNCTIONS][FBSState.REQUIREMENTS] != base_matrix[FBSState.FUNCTIONS][FBSState.REQUIREMENTS] * AI_REWORK
    
    for row in modified:
        assert sum(row) - 1.0 < 1e-6


def test_apply_ai_modifiers_clamping_and_normalization() -> None:
    """Test clamping to [0,1] and row normalization."""
    # Matrix that will easily exceed 1.0 when multiplied by AI_SPEED (4.0)
    base_matrix = [
        [0.1, 0.9, 0.0, 0.0, 0.0],  # 0.9 * 4.0 = 3.6 -> non_diagonal_sum > 1.0
        [0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 1.0],
    ]
    
    modified = apply_ai_modifiers(base_matrix, AIMode.AI_RAW)
    
    # The value 3.6 gets clamped to 1.0, then row normalized to [0, 1.0, 0, 0, 0]
    assert modified[0][1] <= 1.0
    assert sum(modified[0]) - 1.0 < 1e-6
