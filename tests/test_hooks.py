# tests/test_hooks.py
from waspnest.hooks import Hooks, HookPoint
import pytest
from unittest.mock import Mock

@pytest.fixture
def hooks():
    return Hooks()

def test_hook_registration(hooks):
    """Test basic hook registration"""
    mock_callback = Mock()
    hooks.on(HookPoint.PRE_EXECUTE, mock_callback)
    
    assert mock_callback in hooks.hooks[HookPoint.PRE_EXECUTE]

def test_hook_triggering(hooks):
    """Test hook triggering with arguments"""
    mock_callback = Mock()
    hooks.on(HookPoint.PRE_EXECUTE, mock_callback)
    
    test_args = {"state": "test_state"}
    hooks.trigger(HookPoint.PRE_EXECUTE, **test_args)
    
    mock_callback.assert_called_once_with(**test_args)

def test_multiple_hooks(hooks):
    """Test multiple hooks on same point"""
    mock_callback1 = Mock()
    mock_callback2 = Mock()
    
    hooks.on(HookPoint.ERROR, mock_callback1)
    hooks.on(HookPoint.ERROR, mock_callback2)
    
    test_args = {"exception": "test_error"}
    hooks.trigger(HookPoint.ERROR, **test_args)
    
    mock_callback1.assert_called_once_with(**test_args)
    mock_callback2.assert_called_once_with(**test_args)

def test_hooks_different_points(hooks):
    """Test hooks on different points"""
    mock_pre = Mock()
    mock_post = Mock()
    
    hooks.on(HookPoint.PRE_EXECUTE, mock_pre)
    hooks.on(HookPoint.POST_EXECUTE, mock_post)
    
    hooks.trigger(HookPoint.PRE_EXECUTE, state="test")
    mock_pre.assert_called_once_with(state="test")
    mock_post.assert_not_called()
    
    hooks.trigger(HookPoint.POST_EXECUTE, state="test")
    mock_post.assert_called_once_with(state="test")

def test_hook_error_handling(hooks):
    """Test that error in one hook doesn't affect others"""
    def error_hook(**kwargs):
        raise ValueError("Hook error")
    
    mock_callback = Mock()
    
    hooks.on(HookPoint.PRE_EXECUTE, error_hook)
    hooks.on(HookPoint.PRE_EXECUTE, mock_callback)
    
    # This should not raise an exception
    hooks.trigger(HookPoint.PRE_EXECUTE, state="test")
    
    # Second hook should still be called
    mock_callback.assert_called_once_with(state="test")