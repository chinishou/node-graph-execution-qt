"""
Test Optimizations
==================

Test all the JSON serialization optimizations:
1. Integer ID system (replacing UUID)
2. Position precision (2 decimal places)
3. Empty value removal (null, "", [], {})
4. JSON minification (no whitespace)
5. Subnet I/O node default positions
"""

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from nodegraph.core.models import NodeModel, NetworkModel
from nodegraph.nodes.subnet import SubnetNode
from nodegraph.nodes.base import FloatVariable
from nodegraph.nodes.operators import AddNode
from nodegraph.core.serialization import JSONSerializer


def test_integer_id_system():
    """Test that node IDs are integers starting from 0."""
    # Reset ID counter by importing fresh
    import nodegraph.core.models.node_model as nm
    nm._next_node_id = 0

    # Create nodes
    n1 = NodeModel(name="Node1")
    n2 = NodeModel(name="Node2")
    subnet = SubnetNode(name="Subnet1")
    n3 = NodeModel(name="Node3")

    # Check IDs are integers
    assert isinstance(n1.id, int), "ID should be int"
    assert isinstance(n2.id, int), "ID should be int"
    assert isinstance(subnet.id, int), "ID should be int"

    # Check IDs are sequential
    assert n1.id == 0, f"First node should have ID 0, got {n1.id}"
    assert n2.id == 1, f"Second node should have ID 1, got {n2.id}"
    assert subnet.id == 2, f"Subnet should have ID 2, got {subnet.id}"

    # Check subnet internal nodes
    internal_nodes = subnet.get_internal_network().nodes()
    assert len(internal_nodes) == 2, "Subnet should have 2 internal nodes"
    assert internal_nodes[0].id == 3, "First internal node should have ID 3"
    assert internal_nodes[1].id == 4, "Second internal node should have ID 4"

    # Next node after subnet should have ID 5
    assert n3.id == 5, f"Node after subnet should have ID 5, got {n3.id}"

    print("✓ Integer ID system works correctly")


def test_position_precision():
    """Test that positions are rounded to 2 decimal places."""
    node = NodeModel(name="TestNode")

    # Set position with high precision
    node.set_position(100.123456789, 200.987654321)

    # Serialize
    data = node.serialize()

    # Check position is rounded
    assert data["position"] == [100.12, 200.99], \
        f"Position should be [100.12, 200.99], got {data['position']}"

    # Test trailing zeros removal
    node.set_position(150.0, 250.50)
    data = node.serialize()
    assert data["position"] == [150, 250.5], \
        f"Position should be [150, 250.5], got {data['position']}"

    print("✓ Position precision works correctly")


def test_empty_value_removal():
    """Test that null, empty strings, empty arrays, and empty dicts are removed."""
    node = NodeModel(name="TestNode")

    # Add some parameters and connectors
    node.add_parameter("param1", data_type="float", default_value=1.0)
    node.add_output("output1", data_type="float")

    # Serialize
    data = node.serialize()

    # Check that empty inputs dict is removed
    assert "inputs" not in data or data["inputs"] == {}, \
        "Empty inputs should be removed or empty"

    # Check that color (None) is removed
    assert "color" not in data, "Null color should be removed"

    print("✓ Empty value removal works correctly")


def test_json_minification():
    """Test that JSON is minified by default."""
    import tempfile

    # Create a simple network
    network = NetworkModel(name="TestNetwork")
    var = FloatVariable(default_value=3.14, name="Pi")
    network.add_node(var)

    # Save with default settings (should be minified)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name

    JSONSerializer.save(network, temp_path)

    # Read file content
    with open(temp_path, 'r') as f:
        content = f.read()

    # Check no unnecessary whitespace
    assert '\n' not in content, "Minified JSON should not have newlines"
    assert '  ' not in content, "Minified JSON should not have multiple spaces"

    # Check uses compact separators
    assert ',' in content and ': ' not in content, \
        "Should use compact separators"

    # Parse to verify it's valid JSON
    data = json.loads(content)
    assert data is not None, "Should be valid JSON"

    # Clean up
    Path(temp_path).unlink()

    print("✓ JSON minification works correctly")


def test_subnet_io_positions():
    """Test that subnet I/O nodes have correct default positions."""
    subnet = SubnetNode(name="TestSubnet")
    internal_network = subnet.get_internal_network()

    # Get internal nodes
    nodes = internal_network.nodes()
    assert len(nodes) == 2, "Should have 2 internal nodes"

    # Find input and output nodes
    input_node = next(n for n in nodes if 'Input' in n.name)
    output_node = next(n for n in nodes if 'Output' in n.name)

    # Check positions
    input_pos = input_node.position()
    output_pos = output_node.position()

    assert input_pos == (-200, 0), \
        f"Input node should be at (-200, 0), got {input_pos}"
    assert output_pos == (200, 0), \
        f"Output node should be at (200, 0), got {output_pos}"

    print("✓ Subnet I/O node positions are correct")


def test_complete_roundtrip():
    """Test complete roundtrip with all optimizations."""
    import tempfile
    import nodegraph.core.models.node_model as nm
    from nodegraph.core.registry import NodeRegistry
    nm._next_node_id = 0

    # Register node types for deserialization
    NodeRegistry.register(FloatVariable)
    NodeRegistry.register(AddNode)

    # Create network
    network = NetworkModel(name="OptimizedNetwork")

    # Create nodes
    var_a = FloatVariable(default_value=10.5, name="A")
    var_b = FloatVariable(default_value=20.3, name="B")
    add = AddNode()

    # Set positions
    var_a.set_position(100.123, 150.789)
    var_b.set_position(200.456, 250.012)
    add.set_position(300.999, 350.001)

    # Add to network
    network.add_node(var_a)
    network.add_node(var_b)
    network.add_node(add)

    # Connect
    network.connect(var_a.id, "out", add.id, "a")
    network.connect(var_b.id, "out", add.id, "b")

    # Save to file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name

    JSONSerializer.save(network, temp_path)

    # Read and check file
    with open(temp_path, 'r') as f:
        content = f.read()

    # Verify minification
    assert '\n' not in content, "Should be minified"

    # Verify IDs are integers
    data = json.loads(content)
    assert all(isinstance(n["id"], int) for n in data["network"]["nodes"]), \
        "All node IDs should be integers"

    # Verify position precision
    assert data["network"]["nodes"][0]["position"] == [100.12, 150.79], \
        "Position should be rounded to 2 decimals"

    # Load back
    loaded_network, _ = JSONSerializer.load(temp_path)

    # Verify network
    assert loaded_network.node_count() == 3, "Should have 3 nodes"
    assert len(loaded_network.connector_pairs()) == 2, "Should have 2 connections"

    # Verify nodes
    nodes = loaded_network.nodes()
    assert all(isinstance(n.id, int) for n in nodes), "All IDs should be integers"

    # Verify positions
    node_a = next(n for n in nodes if n.name == "A")
    assert node_a.position() == (100.12, 150.79), \
        f"Position should be (100.12, 150.79), got {node_a.position()}"

    # Clean up
    Path(temp_path).unlink()

    print("✓ Complete roundtrip with all optimizations works")


def run_all_tests():
    """Run all optimization tests."""
    print("=" * 60)
    print("Optimization Tests")
    print("=" * 60)

    test_integer_id_system()
    test_position_precision()
    test_empty_value_removal()
    test_json_minification()
    test_subnet_io_positions()
    test_complete_roundtrip()

    print("=" * 60)
    print("All optimization tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
