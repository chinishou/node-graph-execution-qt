"""
Integration tests for copy-paste functionality.
"""

import pytest
from nodegraph.core.models import NetworkModel
from nodegraph.nodes.base.variable_node import VariableNode
from nodegraph.nodes.operators.math_nodes import AddNode
from nodegraph.nodes.subnet import SubnetNode
from nodegraph.nodes.subnet.subnet_io_nodes import SubnetInputNode, SubnetOutputNode
from nodegraph.core.registry import NodeRegistry


@pytest.fixture(autouse=True)
def register_nodes():
    """Register node types for testing."""
    NodeRegistry.register(VariableNode)
    NodeRegistry.register(AddNode)
    NodeRegistry.register(SubnetNode)
    NodeRegistry.register(SubnetInputNode)
    NodeRegistry.register(SubnetOutputNode)
    yield
    # No cleanup needed - registry persists across tests


def test_serialize_nodes_with_connections():
    """Test serializing nodes preserves connection information."""
    network = NetworkModel("/")

    # Create nodes
    var1 = VariableNode(data_type="int", name="Var1")
    var2 = VariableNode(data_type="int", name="Var2")
    add = AddNode()

    network.add_node(var1)
    network.add_node(var2)
    network.add_node(add)

    # Create connections
    network.connect(var1.id, "out", add.id, "a")
    network.connect(var2.id, "out", add.id, "b")

    # Verify connections exist
    assert len(network._connector_pairs) == 2
    assert var1.output("out").is_connected()
    assert var2.output("out").is_connected()
    assert add.input("a").is_connected()
    assert add.input("b").is_connected()


def test_restore_connections_after_copy():
    """Test that connections can be restored between copied nodes."""
    network = NetworkModel("/")

    # Create original nodes
    var1 = VariableNode(data_type="int", name="Var1")
    var2 = VariableNode(data_type="int", name="Var2")
    add = AddNode()

    network.add_node(var1)
    network.add_node(var2)
    network.add_node(add)

    # Create connections
    network.connect(var1.id, "out", add.id, "a")
    network.connect(var2.id, "out", add.id, "b")

    # Simulate copy: collect node data and connections
    copied_nodes = []
    copied_node_ids = {var1.id, var2.id, add.id}

    for node in [var1, var2, add]:
        node_data = {
            'id': str(node.id),
            'node_type': node.node_type,
            'position': node.position(),
            'parameters': {name: param.value() for name, param in node.parameters().items()},
            'input_defaults': {name: conn.default_value for name, conn in node.inputs().items()}
        }
        copied_nodes.append(node_data)

    # Copy connections
    copied_connections = []
    for source_conn, target_conn in network._connector_pairs:
        if source_conn.node.id in copied_node_ids and target_conn.node.id in copied_node_ids:
            copied_connections.append({
                'source_node_id': str(source_conn.node.id),
                'source_output': source_conn.name,
                'target_node_id': str(target_conn.node.id),
                'target_input': target_conn.name
            })

    assert len(copied_connections) == 2

    # Simulate paste: create new nodes and restore connections
    new_network = NetworkModel("paste_test")
    id_mapping = {}

    for node_data in copied_nodes:
        new_node = NodeRegistry.create_node(node_data['node_type'])
        new_node.set_position(*node_data['position'])
        new_network.add_node(new_node)
        id_mapping[node_data['id']] = new_node

    # Restore connections
    for conn_data in copied_connections:
        source_node = id_mapping[conn_data['source_node_id']]
        target_node = id_mapping[conn_data['target_node_id']]
        new_network.connect(
            source_node.id,
            conn_data['source_output'],
            target_node.id,
            conn_data['target_input']
        )

    # Verify connections were restored
    assert len(new_network._connector_pairs) == 2


def test_subnet_serialize_with_internal_network():
    """Test that SubnetNode serialization preserves internal network."""
    network = NetworkModel("/")

    # Create subnet with internal nodes
    subnet = SubnetNode(name="TestSubnet")
    network.add_node(subnet)

    internal = subnet.get_internal_network()
    var = VariableNode(data_type="int", name="InternalVar")
    internal.add_node(var)

    # Serialize subnet
    subnet_data = subnet.serialize()

    assert 'internal_network' in subnet_data
    assert 'nodes' in subnet_data['internal_network']
    # Should have input1, output1 (auto-created) + InternalVar
    assert len(subnet_data['internal_network']['nodes']) == 3


def test_subnet_deserialize_with_internal_network():
    """Test that SubnetNode deserialization restores internal network."""
    network = NetworkModel("/")

    # Create original subnet
    subnet1 = SubnetNode(name="Original")
    network.add_node(subnet1)

    internal1 = subnet1.get_internal_network()
    var = VariableNode(data_type="int", name="InternalVar")
    var.parameter("value").set_value(42)
    internal1.add_node(var)

    # Serialize
    subnet_data = subnet1.serialize()

    # Deserialize into new subnet
    subnet2 = SubnetNode.deserialize(subnet_data)

    # Verify internal network was restored
    internal2 = subnet2.get_internal_network()
    assert internal2 is not None

    nodes = internal2.nodes()
    # Should have input1, output1, InternalVar
    assert len(nodes) == 3

    # Find InternalVar
    internal_var = internal2.get_node_by_name("InternalVar")
    assert internal_var is not None
    assert internal_var.parameter("value").value() == 42


def test_filter_subnet_io_nodes_from_copy():
    """Test that SubnetInputNode and SubnetOutputNode are filtered during copy."""
    from nodegraph.nodes.subnet.subnet_io_nodes import SubnetInputNode, SubnetOutputNode

    network = NetworkModel("/")
    subnet = SubnetNode(name="TestSubnet")
    network.add_node(subnet)

    internal = subnet.get_internal_network()

    # Get auto-created I/O nodes
    io_nodes = [node for node in internal.nodes()
                if isinstance(node, (SubnetInputNode, SubnetOutputNode))]

    assert len(io_nodes) == 2  # input1 and output1

    # Simulate filtering logic from copy
    selected_nodes = internal.nodes()
    filtered_nodes = [node for node in selected_nodes
                      if not isinstance(node, (SubnetInputNode, SubnetOutputNode))]

    # All I/O nodes should be filtered out
    assert len(filtered_nodes) == 0
    assert len(io_nodes) == 2


def test_copy_preserves_parameter_values():
    """Test that parameter values are preserved during copy."""
    network = NetworkModel("/")

    var = VariableNode(data_type="int", name="Var")
    var.parameter("value").set_value(123)
    network.add_node(var)

    # Simulate copy
    node_data = {
        'node_type': var.node_type,
        'parameters': {name: param.value() for name, param in var.parameters().items()}
    }

    # Simulate paste
    new_var = NodeRegistry.create_node(node_data['node_type'])
    for name, value in node_data['parameters'].items():
        param = new_var.parameter(name)
        if param:
            param.set_value(value)

    assert new_var.parameter("value").value() == 123


def test_copy_preserves_input_defaults():
    """Test that input default values are preserved during copy."""
    network = NetworkModel("/")

    add = AddNode()
    add.input("a").default_value = 10
    add.input("b").default_value = 20
    network.add_node(add)

    # Simulate copy
    node_data = {
        'node_type': add.node_type,
        'input_defaults': {name: conn.default_value for name, conn in add.inputs().items()}
    }

    # Simulate paste
    new_add = NodeRegistry.create_node(node_data['node_type'])
    for name, value in node_data['input_defaults'].items():
        connector = new_add.input(name)
        if connector:
            connector.default_value = value

    assert new_add.input("a").default_value == 10
    assert new_add.input("b").default_value == 20
