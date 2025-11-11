"""Test signal emission directly."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from nodegraph.core.models import ParameterModel

# Create a simple parameter
param = ParameterModel(name="test", data_type="float", default_value=1.0)

print(f"Initial value: {param.value()}")

# Connect a callback
callbacks_triggered = []

def on_value_changed(value):
    callbacks_triggered.append(("with_arg", value))
    print(f"Callback with arg triggered: {value}")

param.value_changed.connect(on_value_changed)

# Change value
print(f"\nChanging value to 2.0...")
param.set_value(2.0)

print(f"New value: {param.value()}")
print(f"Callbacks triggered: {callbacks_triggered}")

# Try changing to same value
print(f"\nChanging value to 2.0 again (same value)...")
callbacks_triggered.clear()
param.set_value(2.0)
print(f"Callbacks triggered: {callbacks_triggered}")

# Change to different value
print(f"\nChanging value to 3.0...")
callbacks_triggered.clear()
param.set_value(3.0)
print(f"New value: {param.value()}")
print(f"Callbacks triggered: {callbacks_triggered}")
