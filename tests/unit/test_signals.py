"""
Tests for Signal System
========================

Test the signal/slot system including:
- Signal emission and callback execution
- Multiple listener registration
- Weak reference cleanup
- Disconnection functionality
- Error handling in callbacks
- Argument passing
"""

import sys
from pathlib import Path
import gc

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodegraph.core.signals import Signal


def test_signal_creation():
    """Test creating a signal."""
    signal = Signal()

    assert len(signal) == 0

    print("✓ Signal creation works")


def test_signal_emit_no_slots():
    """Test emitting a signal with no connected slots."""
    signal = Signal()

    # Should not raise error
    signal.emit()
    signal.emit(1, 2, 3)
    signal.emit(foo="bar")

    print("✓ Signal emit with no slots works")


def test_signal_connect_function():
    """Test connecting a function to a signal."""
    signal = Signal()
    calls = []

    def callback():
        calls.append("called")

    signal.connect(callback)
    assert len(signal) == 1

    signal.emit()
    assert len(calls) == 1
    assert calls[0] == "called"

    print("✓ Signal connect function works")


def test_signal_connect_method():
    """Test connecting a method to a signal."""
    signal = Signal()

    class Listener:
        def __init__(self):
            self.calls = []

        def callback(self):
            self.calls.append("called")

    listener = Listener()
    signal.connect(listener.callback)
    assert len(signal) == 1

    signal.emit()
    assert len(listener.calls) == 1

    print("✓ Signal connect method works")


def test_signal_multiple_slots():
    """Test connecting multiple slots to a signal."""
    signal = Signal()
    calls = []

    def callback1():
        calls.append("callback1")

    def callback2():
        calls.append("callback2")

    def callback3():
        calls.append("callback3")

    signal.connect(callback1)
    signal.connect(callback2)
    signal.connect(callback3)

    assert len(signal) == 3

    signal.emit()

    assert len(calls) == 3
    assert "callback1" in calls
    assert "callback2" in calls
    assert "callback3" in calls

    print("✓ Signal multiple slots work")


def test_signal_disconnect():
    """Test disconnecting a slot from a signal."""
    signal = Signal()
    calls = []

    def callback():
        calls.append("called")

    signal.connect(callback)
    assert len(signal) == 1

    signal.emit()
    assert len(calls) == 1

    # Disconnect
    signal.disconnect(callback)
    assert len(signal) == 0

    # Should not be called
    signal.emit()
    assert len(calls) == 1  # Still 1, not 2

    print("✓ Signal disconnect works")


def test_signal_disconnect_method():
    """Test disconnecting a method from a signal."""
    signal = Signal()

    class Listener:
        def __init__(self):
            self.calls = []

        def callback(self):
            self.calls.append("called")

    listener = Listener()
    signal.connect(listener.callback)

    signal.emit()
    assert len(listener.calls) == 1

    signal.disconnect(listener.callback)
    assert len(signal) == 0

    signal.emit()
    assert len(listener.calls) == 1  # Still 1

    print("✓ Signal disconnect method works")


def test_signal_with_arguments():
    """Test signal emission with arguments."""
    signal = Signal()
    results = []

    def callback(a, b, c):
        results.append(a + b + c)

    signal.connect(callback)
    signal.emit(1, 2, 3)

    assert len(results) == 1
    assert results[0] == 6

    print("✓ Signal with arguments works")


def test_signal_with_kwargs():
    """Test signal emission with keyword arguments."""
    signal = Signal()
    results = []

    def callback(x=0, y=0):
        results.append(x * y)

    signal.connect(callback)
    signal.emit(x=5, y=3)

    assert len(results) == 1
    assert results[0] == 15

    print("✓ Signal with kwargs works")


def test_signal_weak_reference_cleanup():
    """Test that weak references are cleaned up when objects are deleted."""
    signal = Signal()

    class Listener:
        def __init__(self):
            self.calls = []

        def callback(self):
            self.calls.append("called")

    # Create listener and connect
    listener = Listener()
    signal.connect(listener.callback)
    assert len(signal) == 1

    # Emit should work
    signal.emit()
    assert len(listener.calls) == 1

    # Delete listener
    del listener
    gc.collect()  # Force garbage collection

    # Signal should clean up dead reference
    signal.emit()
    assert len(signal) == 0

    print("✓ Signal weak reference cleanup works")


def test_signal_error_in_slot():
    """Test that errors in one slot don't prevent other slots from being called."""
    signal = Signal()
    calls = []

    def callback1():
        calls.append("callback1")

    def callback_error():
        raise ValueError("Test error")

    def callback2():
        calls.append("callback2")

    signal.connect(callback1)
    signal.connect(callback_error)
    signal.connect(callback2)

    # Should not raise, and both callback1 and callback2 should be called
    signal.emit()

    assert "callback1" in calls
    assert "callback2" in calls

    print("✓ Signal error handling works")


def test_signal_slot_without_arguments():
    """Test calling a slot that doesn't accept arguments."""
    signal = Signal()
    calls = []

    def callback():
        calls.append("called")

    signal.connect(callback)

    # Emit with arguments - signal should try calling without args
    signal.emit(1, 2, 3)

    assert len(calls) == 1

    print("✓ Signal slot without arguments works")


def test_signal_lambda():
    """Test connecting a lambda function."""
    signal = Signal()
    results = []

    # Store lambda in variable to prevent garbage collection
    # (weak references to inline lambdas will be immediately cleaned up)
    callback = lambda x: results.append(x * 2)
    signal.connect(callback)
    signal.emit(5)

    assert len(results) == 1
    assert results[0] == 10

    print("✓ Signal lambda works")


def test_signal_same_slot_multiple_times():
    """Test connecting the same slot multiple times."""
    signal = Signal()
    calls = []

    def callback():
        calls.append("called")

    signal.connect(callback)
    signal.connect(callback)
    signal.connect(callback)

    # All three connections should be active
    assert len(signal) == 3

    signal.emit()

    # Should be called 3 times
    assert len(calls) == 3

    print("✓ Signal same slot multiple times works")


def test_signal_disconnect_nonexistent():
    """Test disconnecting a slot that was never connected."""
    signal = Signal()

    def callback():
        pass

    # Should not raise error
    signal.disconnect(callback)

    print("✓ Signal disconnect nonexistent slot works")


def test_signal_in_node_system():
    """Test signals in the actual node system."""
    from nodegraph.nodes.base import FloatVariable
    from nodegraph.nodes.operators import AddNode

    # Create node
    var = FloatVariable(default_value=5.0)
    add = AddNode()

    # Track parameter changes
    changes = []

    def on_param_change():
        changes.append("changed")

    # Connect to parameter changed signal
    add.parameter_changed.connect(on_param_change)

    # Modify a parameter (if AddNode has any)
    # For now, just test that the signal exists and works
    add.parameter_changed.emit()

    assert len(changes) == 1

    print("✓ Signal in node system works")


def test_signal_dirty_changed():
    """Test dirty_changed signal in nodes."""
    from nodegraph.nodes.base import FloatVariable

    var = FloatVariable(default_value=5.0)
    var.enable_caching = True  # Enable caching to trigger dirty state

    dirty_states = []

    def on_dirty_changed(is_dirty):
        dirty_states.append(is_dirty)

    var.dirty_changed.connect(on_dirty_changed)

    # Cook the node to make it clean (nodes start dirty)
    var.cook()

    # Should have emitted False (clean)
    assert len(dirty_states) == 1
    assert dirty_states[0] == False

    # Now mark dirty - should emit True
    var.mark_dirty()

    assert len(dirty_states) == 2
    assert dirty_states[1] == True

    print("✓ Signal dirty_changed works")


def run_all_tests():
    """Run all signal tests."""
    print("=" * 60)
    print("Signal Tests")
    print("=" * 60)

    test_signal_creation()
    test_signal_emit_no_slots()
    test_signal_connect_function()
    test_signal_connect_method()
    test_signal_multiple_slots()
    test_signal_disconnect()
    test_signal_disconnect_method()
    test_signal_with_arguments()
    test_signal_with_kwargs()
    test_signal_weak_reference_cleanup()
    test_signal_error_in_slot()
    test_signal_slot_without_arguments()
    test_signal_lambda()
    test_signal_same_slot_multiple_times()
    test_signal_disconnect_nonexistent()
    test_signal_in_node_system()
    test_signal_dirty_changed()

    print("=" * 60)
    print("All signal tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
