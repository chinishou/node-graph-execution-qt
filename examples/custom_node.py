"""
Custom Node Example
====================

This example shows how to create custom nodes.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nodegraph.nodes.base import BaseNode
from nodegraph.core.models import NetworkModel
from nodegraph.core.registry import NodeRegistry
from typing import Dict, Any


# Example 1: Simple custom node
class SquareNode(BaseNode):
    """Node that squares a number."""

    category = "Math"
    description = "Calculate the square of a number"

    def __init__(self, **kwargs):
        super().__init__(name="Square", node_type="SquareNode", **kwargs)

    def setup(self):
        """Define node interface."""
        self.add_input("value", data_type="float", default_value=0.0)
        self.add_output("result", data_type="float")

    def compute(self, **inputs) -> Dict[str, Any]:
        """Square the input value."""
        value = inputs.get("value", 0.0)
        result = value ** 2
        return {"result": result}


# Example 2: Node with parameters
class ClampNode(BaseNode):
    """Node that clamps a value between min and max."""

    category = "Math"
    description = "Clamp a value between minimum and maximum"

    def __init__(self, **kwargs):
        super().__init__(name="Clamp", node_type="ClampNode", **kwargs)

    def setup(self):
        """Define node interface."""
        self.add_input("value", data_type="float", default_value=0.0)
        self.add_output("result", data_type="float")

        # Add parameters
        self.add_parameter("min", data_type="float", default_value=0.0, display_name="Minimum")
        self.add_parameter("max", data_type="float", default_value=1.0, display_name="Maximum")

    def compute(self, **inputs) -> Dict[str, Any]:
        """Clamp the input value."""
        value = inputs.get("value", 0.0)
        min_val = self.parameter("min").value()
        max_val = self.parameter("max").value()

        result = max(min_val, min(max_val, value))
        return {"result": result}


# Example 3: Node with multiple inputs/outputs
class MinMaxNode(BaseNode):
    """Node that outputs both minimum and maximum of inputs."""

    category = "Math"
    description = "Find minimum and maximum of multiple values"

    def __init__(self, **kwargs):
        super().__init__(name="MinMax", node_type="MinMaxNode", **kwargs)

    def setup(self):
        """Define node interface."""
        self.add_input("a", data_type="float", default_value=0.0)
        self.add_input("b", data_type="float", default_value=0.0)
        self.add_input("c", data_type="float", default_value=0.0)

        self.add_output("min", data_type="float")
        self.add_output("max", data_type="float")
        self.add_output("average", data_type="float")

    def compute(self, **inputs) -> Dict[str, Any]:
        """Calculate min, max, and average."""
        values = [
            inputs.get("a", 0.0),
            inputs.get("b", 0.0),
            inputs.get("c", 0.0),
        ]

        return {
            "min": min(values),
            "max": max(values),
            "average": sum(values) / len(values),
        }


def main():
    print("=" * 60)
    print("Custom Node Example")
    print("=" * 60)
    print()

    # Register custom nodes
    print("1. Registering custom nodes...")
    NodeRegistry.register(SquareNode)
    NodeRegistry.register(ClampNode)
    NodeRegistry.register(MinMaxNode)
    print(f"   Registered {len(NodeRegistry.get_all_nodes())} node types")
    print()

    # Test SquareNode
    print("2. Testing SquareNode...")
    square = NodeRegistry.create_node("SquareNode")
    square.input("value").default_value = 5.0
    square.cook()
    result = square.get_output_value("result")
    print(f"   Square of 5.0 = {result}")
    print()

    # Test ClampNode
    print("3. Testing ClampNode...")
    clamp = NodeRegistry.create_node("ClampNode")
    clamp.input("value").default_value = 150.0
    clamp.parameter("min").set_value(0.0)
    clamp.parameter("max").set_value(100.0)
    clamp.cook()
    result = clamp.get_output_value("result")
    print(f"   Clamp 150.0 between 0.0 and 100.0 = {result}")
    print()

    # Test MinMaxNode
    print("4. Testing MinMaxNode...")
    minmax = NodeRegistry.create_node("MinMaxNode")
    minmax.input("a").default_value = 10.0
    minmax.input("b").default_value = 25.0
    minmax.input("c").default_value = 15.0
    minmax.cook()
    min_val = minmax.get_output_value("min")
    max_val = minmax.get_output_value("max")
    avg_val = minmax.get_output_value("average")
    print(f"   Values: 10.0, 25.0, 15.0")
    print(f"   Min: {min_val}")
    print(f"   Max: {max_val}")
    print(f"   Average: {avg_val}")
    print()

    # Create a network using custom nodes
    print("5. Creating network with custom nodes...")
    network = NetworkModel(name="Custom Node Network")

    # Add nodes
    network.add_node(square)
    network.add_node(clamp)
    network.add_node(minmax)

    # Connect: square -> clamp -> minmax
    network.connect(square.id, "result", clamp.id, "value")
    network.connect(clamp.id, "result", minmax.id, "a")

    print(f"   Network has {network.node_count()} nodes and {len(network.connections())} connections")
    print()

    print("=" * 60)
    print("Custom node example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
