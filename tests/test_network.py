"""
Tests for NetworkModel
======================

Test the network management system including:
- Node management (add/remove)
- Connection management
- Network execution
- Topological sorting
- Network serialization
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodegraph.core.models import NetworkModel, NodeModel
from nodegraph.nodes.base import FloatVariable, IntVariable
from nodegraph.nodes.operators import AddNode, MultiplyNode


def test_network_creation():
    """Test creating a network."""
    network = NetworkModel(name="TestNetwork")

    assert network.name == "TestNetwork"
    assert len(network.nodes()) == 0
    assert len(network.connections()) == 0

    print("✓ Network creation works")


def test_add_remove_nodes():
    """Test adding and removing nodes from network."""
    network = NetworkModel(name="TestNetwork")

    # Add nodes
    node1 = FloatVariable(default_value=1.0, name="Var1")
    node2 = AddNode()

    network.add_node(node1)
    network.add_node(node2)

    assert len(network.nodes()) == 2
    assert node1 in network.nodes()
    assert node2 in network.nodes()
    assert node1.network == network
    assert node2.network == network

    # Remove node
    network.remove_node(node1.id)
    assert len(network.nodes()) == 1
    assert node1 not in network.nodes()

    print("✓ Add/remove nodes works")


def test_connect_disconnect():
    """Test connecting and disconnecting nodes."""
    network = NetworkModel(name="TestNetwork")

    # Create and add nodes
    var1 = FloatVariable(default_value=5.0, name="A")
    var2 = FloatVariable(default_value=3.0, name="B")
    add = AddNode()

    network.add_node(var1)
    network.add_node(var2)
    network.add_node(add)

    # Connect nodes through network
    network.connect(var1.id, "out", add.id, "a")
    network.connect(var2.id, "out", add.id, "b")

    assert len(network.connections()) == 2
    assert var1.output("out").is_connected()
    assert var2.output("out").is_connected()
    assert add.input("a").is_connected()
    assert add.input("b").is_connected()

    # Disconnect
    network.disconnect(var1.id, "out", add.id, "a")

    assert len(network.connections()) == 1
    assert not var1.output("out").is_connected()
    assert not add.input("a").is_connected()

    print("✓ Connect/disconnect works")


def test_network_execution():
    """Test executing a network."""
    network = NetworkModel(name="TestNetwork")

    # Build network: (A + B) * C
    var_a = FloatVariable(default_value=2.0, name="A")
    var_b = FloatVariable(default_value=3.0, name="B")
    var_c = FloatVariable(default_value=4.0, name="C")
    add = AddNode()
    mul = MultiplyNode()

    network.add_node(var_a)
    network.add_node(var_b)
    network.add_node(var_c)
    network.add_node(add)
    network.add_node(mul)

    network.connect(var_a.id, "out", add.id, "a")
    network.connect(var_b.id, "out", add.id, "b")
    network.connect(add.id, "result", mul.id, "a")
    network.connect(var_c.id, "out", mul.id, "b")

    # Execute the final node (this will cook all parent nodes)
    mul.execute()

    # Check result: (2 + 3) * 4 = 20
    result = mul.get_output_value("result")
    assert result == 20.0

    print("✓ Network execution works")


def test_parent_child_nodes():
    """Test finding parent and child nodes."""
    network = NetworkModel(name="TestNetwork")

    # Build linear network: A -> B -> C
    var_a = FloatVariable(default_value=1.0, name="A")
    add = AddNode()
    mul = MultiplyNode()

    network.add_node(var_a)
    network.add_node(add)
    network.add_node(mul)

    network.connect(var_a.id, "out", add.id, "a")
    network.connect(add.id, "result", mul.id, "a")

    # Test parent nodes
    parents_mul = network.find_parent_nodes(mul)
    assert len(parents_mul) == 1
    assert add in parents_mul

    parents_add = network.find_parent_nodes(add)
    assert len(parents_add) == 1
    assert var_a in parents_add

    # Test child nodes
    children_var = network.find_child_nodes(var_a)
    assert len(children_var) == 1
    assert add in children_var

    children_add = network.find_child_nodes(add)
    assert len(children_add) == 1
    assert mul in children_add

    print("✓ Parent/child nodes work")


def test_get_node():
    """Test getting nodes by ID."""
    network = NetworkModel(name="TestNetwork")

    node1 = FloatVariable(default_value=1.0, name="Node1")
    network.add_node(node1)

    # Get by ID
    retrieved = network.get_node(node1.id)
    assert retrieved is node1

    # Non-existent node
    assert network.get_node("nonexistent") is None

    print("✓ Get node works")


def test_clear_network():
    """Test clearing all nodes and connections."""
    network = NetworkModel(name="TestNetwork")

    # Add some nodes
    var1 = FloatVariable(default_value=1.0)
    var2 = FloatVariable(default_value=2.0)
    add = AddNode()

    network.add_node(var1)
    network.add_node(var2)
    network.add_node(add)

    network.connect(var1.id, "out", add.id, "a")

    assert len(network.nodes()) == 3
    assert len(network.connections()) == 1

    # Clear network
    network.clear()

    assert len(network.nodes()) == 0
    assert len(network.connections()) == 0

    print("✓ Clear network works")


def test_network_serialization():
    """Test network serialization and deserialization."""
    # Create network
    network = NetworkModel(name="TestNetwork")

    var_a = FloatVariable(default_value=10.0, name="A")
    var_b = FloatVariable(default_value=5.0, name="B")
    add = AddNode()

    network.add_node(var_a)
    network.add_node(var_b)
    network.add_node(add)

    network.connect(var_a.id, "out", add.id, "a")
    network.connect(var_b.id, "out", add.id, "b")

    # Serialize
    data = network.serialize()

    assert data["name"] == "TestNetwork"
    assert len(data["nodes"]) == 3
    assert len(data["connections"]) == 2

    # Deserialize (note: full node type restoration requires a node registry)
    network2 = NetworkModel.deserialize(data)

    assert network2.name == "TestNetwork"
    assert len(network2.nodes()) == 3
    assert len(network2.connections()) == 2

    # Verify node IDs are preserved
    assert network2.get_node(var_a.id) is not None
    assert network2.get_node(var_b.id) is not None
    assert network2.get_node(add.id) is not None

    print("✓ Network serialization works")


def test_remove_node_with_connections():
    """Test removing a node removes its connections."""
    network = NetworkModel(name="TestNetwork")

    var1 = FloatVariable(default_value=1.0)
    add = AddNode()

    network.add_node(var1)
    network.add_node(add)

    network.connect(var1.id, "out", add.id, "a")

    assert len(network.connections()) == 1

    # Remove var1 should also remove the connection
    network.remove_node(var1.id)

    assert len(network.connections()) == 0
    assert not add.input("a").is_connected()

    print("✓ Remove node with connections works")


def run_all_tests():
    """Run all network tests."""
    print("=" * 60)
    print("NetworkModel Tests")
    print("=" * 60)

    test_network_creation()
    test_add_remove_nodes()
    test_connect_disconnect()
    test_network_execution()
    test_parent_child_nodes()
    test_get_node()
    test_clear_network()
    test_network_serialization()
    test_remove_node_with_connections()

    print("=" * 60)
    print("All NetworkModel tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
