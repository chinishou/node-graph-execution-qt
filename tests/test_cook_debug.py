"""
Debug script for testing node cooking functionality.

This script helps verify that nodes are properly computing their outputs.
"""

import sys
import os

# Add parent directory to path to import nodegraph
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nodegraph.nodes.operators import AddNode


def test_basic_cooking():
    """Test basic node cooking."""
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

    assert result == 30.0, f"Expected 30.0, got {result}"
    print("\n✅ Test passed!")


def test_node_connection():
    """Test cooking with node connections."""
    from nodegraph.core.models import NetworkModel
    from nodegraph.nodes.operators import MultiplyNode

    # Create network
    network = NetworkModel("Test Network")

    # Create nodes
    add_node = AddNode()
    add_node.name = "Add"
    add_node.input("a").default_value = 5.0
    add_node.input("b").default_value = 3.0

    multiply_node = MultiplyNode()
    multiply_node.name = "Multiply"
    multiply_node.input("b").default_value = 2.0

    # Add to network
    network.add_node(add_node)
    network.add_node(multiply_node)

    # Connect nodes
    network.connect(add_node.id, "result", multiply_node.id, "a")

    print("\n--- Testing Node Connection ---")
    print(f"Network: {network}")
    print(f"Connections: {len(network.connections())}")

    # Cook
    add_node.cook()
    add_result = add_node.get_output_value("result")
    print(f"Add result: {add_result}")

    multiply_node.cook()
    multiply_result = multiply_node.get_output_value("result")
    print(f"Multiply result: {multiply_result}")

    expected = (5.0 + 3.0) * 2.0  # 16.0
    assert multiply_result == expected, f"Expected {expected}, got {multiply_result}"
    print("✅ Connection test passed!")


if __name__ == "__main__":
    print("=" * 60)
    print("Node Cook Debug Tests")
    print("=" * 60)
    print()

    test_basic_cooking()
    test_node_connection()

    print()
    print("=" * 60)
    print("All tests passed!")
    print("=" * 60)
