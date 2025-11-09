"""
Basic Network Example
======================

This example demonstrates the core functionality of the node graph system:
- Creating a network
- Adding nodes
- Connecting nodes
- Executing (cooking) the network
- Saving/loading to JSON
- Exporting to Python code
"""

import sys
import os

# Add parent directory to path to import nodegraph
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nodegraph.core.models import NetworkModel
from nodegraph.core.registry import NodeRegistry
from nodegraph.core.serialization import JSONSerializer, PythonExporter
from nodegraph.nodes.operators import AddNode, MultiplyNode
from nodegraph.nodes.base import PythonNode


def main():
    print("=" * 60)
    print("Node Graph Execution Qt - Basic Network Example")
    print("=" * 60)
    print()

    # Register nodes
    print("1. Registering nodes...")
    NodeRegistry.register(AddNode)
    NodeRegistry.register(MultiplyNode)
    NodeRegistry.register(PythonNode)
    print(f"   Registered {len(NodeRegistry.get_all_nodes())} node types")
    print()

    # Create network
    print("2. Creating network...")
    network = NetworkModel(name="Basic Math Network")

    # Create nodes
    add_node = NodeRegistry.create_node("AddNode")
    add_node.name = "Add_1"
    add_node.set_position(100, 100)

    multiply_node = NodeRegistry.create_node("MultiplyNode")
    multiply_node.name = "Multiply_1"
    multiply_node.set_position(300, 100)

    # Add nodes to network
    network.add_node(add_node)
    network.add_node(multiply_node)

    print(f"   Created network with {network.node_count()} nodes")
    print()

    # Set parameters
    print("3. Setting parameters...")
    # Set default values via inputs
    add_node.input("a").default_value = 10.0
    add_node.input("b").default_value = 20.0
    multiply_node.input("b").default_value = 2.0

    print(f"   Add node: a={add_node.input('a').default_value}, b={add_node.input('b').default_value}")
    print(f"   Multiply node: b={multiply_node.input('b').default_value}")
    print()

    # Connect nodes
    print("4. Connecting nodes...")
    success = network.connect(
        source_node_id=add_node.id,
        source_output="result",
        target_node_id=multiply_node.id,
        target_input="a"
    )
    print(f"   Connection created: {success}")
    print(f"   Total connections: {len(network.connections())}")
    print()

    # Execute network
    print("5. Executing network...")
    print(f"   Cooking Add node...")
    add_node.cook()
    add_result = add_node.get_output_value("result")
    print(f"   Add result: {add_result}")

    print(f"   Cooking Multiply node...")
    multiply_node.cook()
    multiply_result = multiply_node.get_output_value("result")
    print(f"   Multiply result: {multiply_result}")
    print()

    # Save to JSON
    print("6. Saving network to JSON...")
    json_file = "/tmp/test_network.json"
    JSONSerializer.save(network, json_file)
    print(f"   Saved to: {json_file}")
    print()

    # Load from JSON
    print("7. Loading network from JSON...")
    loaded_network = JSONSerializer.load(json_file)
    print(f"   Loaded network: {loaded_network.name}")
    print(f"   Nodes: {loaded_network.node_count()}")
    print(f"   Connections: {len(loaded_network.connections())}")
    print()

    # Export to Python
    print("8. Exporting to Python code...")
    python_code = PythonExporter.export(network, function_name="run_math_network")
    python_file = "/tmp/generated_network.py"
    with open(python_file, 'w') as f:
        f.write(python_code)
    print(f"   Exported to: {python_file}")
    print()

    # Show node registry info
    print("9. Node registry info...")
    for category in NodeRegistry.get_categories():
        print(f"   Category: {category}")
        nodes = NodeRegistry.get_nodes_by_category(category)
        for node_type in nodes:
            info = NodeRegistry.get_node_info(node_type)
            print(f"      - {node_type}: {info['description']}")
    print()

    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
