# tests/test_state.py
import pytest
from dataclasses import FrozenInstanceError
from waspnest.core.state import State
from conftest import QueryInput

def test_state_creation(sample_state):
    """Test basic state creation with proper initialization"""
    assert sample_state.data.text == "test query"
    assert sample_state.context == {"user_id": "123"}
    assert sample_state.metadata == {"source": "test"}

def test_state_with_context(sample_state):
    """Test context updates create new state properly"""
    new_state = sample_state.with_context(session_id="abc")
    
    # Verify new state has combined context
    assert new_state.data == sample_state.data
    assert new_state.context == {"user_id": "123", "session_id": "abc"}
    
    # Verify original state is unchanged
    assert sample_state.context == {"user_id": "123"}

def test_state_immutability(sample_state):
    """Test state immutability guarantees"""
    # Test instance immutability
    with pytest.raises(FrozenInstanceError):
        sample_state.context = {}
    
    with pytest.raises(FrozenInstanceError):
        sample_state.metadata = {}

def test_state_none_values():
    """Test state creation with None values"""
    state = State(QueryInput(text="test"))
    assert state.metadata == {}
    assert state.context == {}