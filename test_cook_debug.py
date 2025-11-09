"""Debug cook functionality"""

import sys
sys.path.insert(0, '.')

from nodegraph.nodes.operators import AddNode

# Create node
node = AddNode()
print(f"Node created: {node}")
print(f"Node inputs: {list(node.inputs().keys())}")
print(f"Node outputs: {list(node.outputs().keys())}")

# Set input values
node.input("a").default_value = 10.0
node.input("b").default_value = 20.0

print(f"\nInput a value: {node.input('a').get_value()}")
print(f"Input b value: {node.input('b').get_value()}")

# Cook
print(f"\nCooking node...")
print(f"Is dirty before cook: {node.is_dirty()}")

success = node.cook()
print(f"Cook success: {success}")
print(f"Is dirty after cook: {node.is_dirty()}")

# Check cached outputs
print(f"\nCached outputs: {node._cached_outputs}")

# Get output
result = node.get_output_value("result")
print(f"Result: {result}")

# Try calling cook directly
print(f"\nCalling cook() method directly:")
direct_result = node.cook(a=5.0, b=3.0)
print(f"Direct result: {direct_result}")
