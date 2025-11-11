"""Test signal connection."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from nodegraph.nodes.base import FloatVariable

# Create a variable
var = FloatVariable(default_value=3.14, name="Test")

# Check parameter
param = var.parameter("value")
print(f"Parameter: {param}")
print(f"Parameter value_changed signal: {param.value_changed}")
print(f"Number of connections: {len(param.value_changed)}")

# Add a test callback
def on_value_changed(value):
    print(f"  >>> Callback triggered! New value: {value}")

# Also add a no-arg callback to test
def on_value_changed_no_arg():
    print(f"  >>> No-arg callback triggered!")

param.value_changed.connect(on_value_changed)
param.value_changed.connect(on_value_changed_no_arg)
print(f"After adding test callbacks, connections: {len(param.value_changed)}")

# Change value
print(f"\nChanging value from {param.value()} to 2.718...")
param.set_value(2.718)

print(f"Value after set: {param.value()}")
print(f"Node dirty state: {var.is_dirty()}")
