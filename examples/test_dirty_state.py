"""Test dirty state propagation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from nodegraph.nodes.base import FloatVariable

# Create a variable
var = FloatVariable(default_value=3.14, name="Test")

# Check initial state
print(f"Initial value: {var.parameter('value').value()}")
print(f"Initial dirty state: {var.is_dirty()}")

# Cook the node
var.cook()
print(f"\nAfter cooking:")
print(f"Output value: {var.get_output_value('out')}")
print(f"Dirty state: {var.is_dirty()}")

# Change the parameter
print(f"\nChanging parameter value to 2.718...")
var.parameter("value").set_value(2.718)

# Check dirty state
print(f"Parameter value: {var.parameter('value').value()}")
print(f"Dirty state after parameter change: {var.is_dirty()}")

# Get output (should trigger recook)
print(f"\nGetting output value (should trigger recook)...")
output = var.get_output_value("out")
print(f"Output value: {output}")
print(f"Dirty state: {var.is_dirty()}")
