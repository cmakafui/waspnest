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
    """Test multiple hooks for the same event"""
    mock_callback1 = Mock()
    mock_callback2 = Mock()

    hooks.on(HookPoint.ERROR, mock_callback1)
    hooks.on(HookPoint.ERROR, mock_callback2)

    test_args = {"exception": ValueError("Test error")}
    hooks.trigger(HookPoint.ERROR, **test_args)

    assert mock_callback1.call_count == 1
    assert mock_callback2.call_count == 1
    mock_callback1.assert_called_with(**test_args)
    mock_callback2.assert_called_with(**test_args)


def test_hook_error_handling(hooks):
    """Test error handling in hooks"""

    def error_hook(**kwargs):
        raise ValueError("Hook error")

    mock_success = Mock()

    hooks.on(HookPoint.PRE_EXECUTE, error_hook)
    hooks.on(HookPoint.PRE_EXECUTE, mock_success)

    # Should not raise exception and should call all hooks
    hooks.trigger(HookPoint.PRE_EXECUTE, state="test")

    mock_success.assert_called_once_with(state="test")


def test_hook_execution_order(hooks):
    """Test hooks execute in registration order"""
    call_order = []

    def hook1(**kwargs):
        call_order.append(1)

    def hook2(**kwargs):
        call_order.append(2)

    hooks.on(HookPoint.PRE_EXECUTE, hook1)
    hooks.on(HookPoint.PRE_EXECUTE, hook2)

    hooks.trigger(HookPoint.PRE_EXECUTE)
    assert call_order == [1, 2]
