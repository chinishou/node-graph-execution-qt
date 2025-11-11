"""Test Signal class directly."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from nodegraph.core.signals import Signal

# Create a signal
signal = Signal()

# Connect callbacks
call_log = []

def callback_with_arg(value):
    call_log.append(("with_arg", value))
    print(f"Callback with arg: {value}")

def callback_no_arg():
    call_log.append(("no_arg", None))
    print(f"Callback no arg")

signal.connect(callback_with_arg)
signal.connect(callback_no_arg)

print(f"Connections: {len(signal)}")

# Emit signal
print(f"\nEmitting signal with value 42...")
signal.emit(42)

print(f"\nCall log: {call_log}")
