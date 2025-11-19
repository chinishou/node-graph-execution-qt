"""
Simple signal/slot system for Model layer
==========================================

A lightweight signal system that doesn't depend on Qt to be able to run in the CLI mode.
This allows the Model layer to remain pure Python.
"""

from typing import Callable, List, Any
from weakref import WeakMethod, ref, ReferenceType


class Signal:
    """Simple signal implementation that supports connect/disconnect/emit."""

    def __init__(self):
        self._slots: List[Any] = []

    def connect(self, slot: Callable) -> None:
        """Connect a callable to this signal."""
        # Use weak references to avoid circular references
        try:
            # Try to create a weak reference for methods
            if hasattr(slot, '__self__'):
                weak_slot = WeakMethod(slot, self._cleanup)
            else:
                weak_slot = ref(slot, self._cleanup)
            self._slots.append(weak_slot)
        except TypeError:
            # For built-in functions or lambdas, use strong reference
            self._slots.append(slot)

    def disconnect(self, slot: Callable) -> None:
        """Disconnect a callable from this signal."""
        for i, weak_slot in enumerate(self._slots):
            # Handle both weak and strong references
            if isinstance(weak_slot, (WeakMethod, ref)):
                actual_slot = weak_slot()
            else:
                actual_slot = weak_slot

            if actual_slot == slot:
                self._slots.pop(i)
                break

    def emit(self, *args, **kwargs) -> None:
        """Emit the signal, calling all connected slots."""
        # Clean up dead weak references
        self._slots = [s for s in self._slots if self._is_alive(s)]

        # Call all connected slots
        for weak_slot in self._slots[:]:  # Copy to avoid modification during iteration
            slot = self._get_callable(weak_slot)
            if not slot:
                return

            try:
                slot(*args, **kwargs)
            except TypeError:
                # Try calling without arguments if slot doesn't accept them
                try:
                    slot()
                except Exception as e2:
                    print(f"Error in signal slot: {e2}")
            except Exception as e:
                print(f"Error in signal slot: {e}")

    def _is_alive(self, slot_ref: Any) -> bool:
        """Check if a slot reference is still alive."""
        if isinstance(slot_ref, (WeakMethod, ref)):
            return slot_ref() is not None  # Weak reference
        return True  # Strong reference (always alive)

    def _get_callable(self, slot_ref: Any) -> Callable:
        """Get the actual callable from a reference."""
        if isinstance(slot_ref, (WeakMethod, ref)):
            return slot_ref()  # Dereference weak reference
        return slot_ref  # Strong reference

    def _cleanup(self, dead_ref: ReferenceType[Any]) -> None:
        """Callback when a weakly referenced slot is garbage-collected."""
        try:
            # Remove the dead weak reference from the slot list
            self._slots.remove(dead_ref)
        except ValueError:
            # Might already be removed by multi-threads or emit(), safe to ignore
            pass

    def __len__(self) -> int:
        """Return the number of connected slots."""
        self._slots = [s for s in self._slots if self._is_alive(s)]
        return len(self._slots)
