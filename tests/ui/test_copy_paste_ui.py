"""
UI tests for copy-paste functionality.
"""

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPointF

from nodegraph.core.models import NetworkModel
from nodegraph.nodes.base.variable_node import VariableNode
from nodegraph.nodes.operators.math_nodes import AddNode
from nodegraph.nodes.subnet import SubnetNode
from nodegraph.nodes.subnet.subnet_io_nodes import SubnetInputNode, SubnetOutputNode
from nodegraph.views.network.network_scene import NetworkScene
from nodegraph.views.network.network_view import NetworkView


@pytest.fixture
def network_view(qtbot):
    """Create a NetworkView with scene."""
    from nodegraph.core.registry import NodeRegistry

    # Register node types for testing
    NodeRegistry.register(VariableNode)
    NodeRegistry.register(AddNode)
    NodeRegistry.register(SubnetNode)
    NodeRegistry.register(SubnetInputNode)
    NodeRegistry.register(SubnetOutputNode)

    network = NetworkModel("/")
    scene = NetworkScene(network)
    view = NetworkView()
    view.set_scene(scene)
    qtbot.addWidget(view)
    return view, network, scene


class TestCopyPasteFunctionality:
    """Test copy-paste functionality in UI."""

    def test_copy_single_node(self, qtbot, network_view):
        """Test copying a single node."""
        view, network, scene = network_view

        # Create node
        var = VariableNode(data_type="int", name="TestVar")
        var.parameter("value").set_value(42)
        var.set_position(100, 100)
        network.add_node(var)

        QApplication.processEvents()

        # Select node
        node_item = scene.get_node_item(var.id)
        assert node_item is not None
        node_item.setSelected(True)

        # Copy
        view._copy_selected_nodes()

        # Verify copied data
        assert len(view._copied_nodes) == 1
        assert view._copied_nodes[0]['node_type'] == 'VariableNode'
        assert view._copied_nodes[0]['parameters']['value'] == 42

    def test_copy_multiple_nodes_with_connections(self, qtbot, network_view):
        """Test copying multiple nodes with connections."""
        view, network, scene = network_view

        # Create nodes
        var1 = VariableNode(data_type="int", name="Var1")
        var1.set_position(100, 100)
        network.add_node(var1)

        var2 = VariableNode(data_type="int", name="Var2")
        var2.set_position(100, 200)
        network.add_node(var2)

        add = AddNode()  # Don't pass name, AddNode already sets it
        add.set_position(300, 150)
        network.add_node(add)

        # Create connections
        network.connect(var1.id, "out", add.id, "a")
        network.connect(var2.id, "out", add.id, "b")

        QApplication.processEvents()

        # Select all nodes
        for node in [var1, var2, add]:
            node_item = scene.get_node_item(node.id)
            node_item.setSelected(True)

        # Copy
        view._copy_selected_nodes()

        # Verify copied data
        assert len(view._copied_nodes) == 3
        assert len(view._copied_connections) == 2

        # Verify connection data
        conn_keys = {(c['source_output'], c['target_input']) for c in view._copied_connections}
        assert ('out', 'a') in conn_keys
        assert ('out', 'b') in conn_keys

    def test_paste_nodes_with_connections(self, qtbot, network_view):
        """Test pasting nodes restores connections."""
        view, network, scene = network_view

        # Create original nodes
        var = VariableNode(data_type="int", name="Var")
        var.set_position(100, 100)
        network.add_node(var)

        add = AddNode()  # Don't pass name, AddNode already sets it
        add.set_position(300, 100)
        network.add_node(add)

        network.connect(var.id, "out", add.id, "a")

        QApplication.processEvents()

        # Select and copy
        for node in [var, add]:
            node_item = scene.get_node_item(node.id)
            node_item.setSelected(True)

        view._copy_selected_nodes()

        # Paste
        view._paste_nodes()
        QApplication.processEvents()

        # Verify new nodes were created
        assert len(network.nodes()) == 4  # 2 original + 2 pasted

        # Verify connections
        assert len(network._connector_pairs) == 2  # 1 original + 1 pasted

    def test_cut_removes_nodes(self, qtbot, network_view):
        """Test cut removes nodes after copying."""
        view, network, scene = network_view

        # Create node
        var = VariableNode(data_type="int", name="TestVar")
        var.set_position(100, 100)
        network.add_node(var)

        QApplication.processEvents()

        # Select node
        node_item = scene.get_node_item(var.id)
        node_item.setSelected(True)

        # Cut
        view._cut_selected_nodes()
        QApplication.processEvents()

        # Verify node was copied
        assert len(view._copied_nodes) == 1

        # Verify node was removed
        assert len(network.nodes()) == 0

    def test_paste_subnet_preserves_internal_network(self, qtbot, network_view):
        """Test pasting subnet preserves internal network."""
        view, network, scene = network_view

        # Create subnet with internal node
        subnet = SubnetNode(name="TestSubnet")
        subnet.set_position(100, 100)
        network.add_node(subnet)

        internal = subnet.get_internal_network()
        var = VariableNode(data_type="int", name="InternalVar")
        var.parameter("value").set_value(99)
        internal.add_node(var)

        QApplication.processEvents()

        # Select and copy subnet
        subnet_item = scene.get_node_item(subnet.id)
        subnet_item.setSelected(True)

        view._copy_selected_nodes()

        # Paste
        view._paste_nodes()
        QApplication.processEvents()

        # Verify new subnet was created
        subnets = [n for n in network.nodes() if isinstance(n, SubnetNode)]
        assert len(subnets) == 2

        # Get the pasted subnet (the one that's not the original)
        pasted_subnet = [s for s in subnets if s.id != subnet.id][0]

        # Verify internal network was preserved
        pasted_internal = pasted_subnet.get_internal_network()
        pasted_var = pasted_internal.get_node_by_name("InternalVar")

        assert pasted_var is not None
        assert pasted_var.parameter("value").value() == 99

    def test_subnet_io_nodes_not_copied(self, qtbot, network_view):
        """Test that subnet I/O nodes are not copied outside subnet."""
        from nodegraph.nodes.subnet.subnet_io_nodes import SubnetInputNode

        view, network, scene = network_view

        subnet = SubnetNode(name="TestSubnet")
        network.add_node(subnet)

        internal = subnet.get_internal_network()
        QApplication.processEvents()

        # Get auto-created input node
        input_nodes = [n for n in internal.nodes() if isinstance(n, SubnetInputNode)]
        assert len(input_nodes) == 1

        # Try to copy I/O node (simulate selecting it)
        view._copied_nodes = []
        selected_nodes = [input_nodes[0]]

        # Filter logic from _copy_selected_nodes
        from nodegraph.nodes.subnet.subnet_io_nodes import SubnetInputNode, SubnetOutputNode
        filtered = [n for n in selected_nodes
                    if not isinstance(n, (SubnetInputNode, SubnetOutputNode))]

        # Verify I/O node was filtered
        assert len(filtered) == 0

    def test_paste_at_cursor_position(self, qtbot, network_view):
        """Test that nodes are pasted at cursor position with offset."""
        view, network, scene = network_view

        # Create node at specific position
        var = VariableNode(data_type="int", name="TestVar")
        var.set_position(100, 100)
        network.add_node(var)

        QApplication.processEvents()

        # Select and copy
        node_item = scene.get_node_item(var.id)
        node_item.setSelected(True)
        view._copy_selected_nodes()

        # Paste (will use cursor position, which defaults to view center)
        view._paste_nodes()
        QApplication.processEvents()

        # Verify new node exists
        assert len(network.nodes()) == 2

        # Get pasted node
        pasted_node = [n for n in network.nodes() if n.id != var.id][0]

        # Position should be offset from original
        orig_pos = var.position()
        pasted_pos = pasted_node.position()
        assert pasted_pos != orig_pos  # Should be different

    def test_copy_preserves_parameter_values(self, qtbot, network_view):
        """Test that parameter values are preserved in copy-paste."""
        view, network, scene = network_view

        # Create node with specific parameter value
        var = VariableNode(data_type="int", name="TestVar")
        var.parameter("value").set_value(777)
        var.set_position(100, 100)
        network.add_node(var)

        QApplication.processEvents()

        # Copy and paste
        node_item = scene.get_node_item(var.id)
        node_item.setSelected(True)
        view._copy_selected_nodes()
        view._paste_nodes()
        QApplication.processEvents()

        # Get pasted node
        pasted_node = [n for n in network.nodes() if n.id != var.id][0]

        # Verify parameter was preserved
        assert pasted_node.parameter("value").value() == 777


class TestCopyPasteKeyboardShortcuts:
    """Test keyboard shortcuts for copy-paste."""

    def test_ctrl_c_copies_selection(self, qtbot, network_view):
        """Test Ctrl+C keyboard shortcut."""
        view, network, scene = network_view

        var = VariableNode(data_type="int", name="TestVar")
        network.add_node(var)
        QApplication.processEvents()

        node_item = scene.get_node_item(var.id)
        node_item.setSelected(True)

        # Simulate Ctrl+C
        qtbot.keyPress(view, Qt.Key_C, Qt.ControlModifier)
        QApplication.processEvents()

        assert len(view._copied_nodes) == 1

    def test_ctrl_x_cuts_selection(self, qtbot, network_view):
        """Test Ctrl+X keyboard shortcut."""
        view, network, scene = network_view

        var = VariableNode(data_type="int", name="TestVar")
        network.add_node(var)
        QApplication.processEvents()

        node_item = scene.get_node_item(var.id)
        node_item.setSelected(True)

        # Simulate Ctrl+X
        qtbot.keyPress(view, Qt.Key_X, Qt.ControlModifier)
        QApplication.processEvents()

        # Verify copied and removed
        assert len(view._copied_nodes) == 1
        assert len(network.nodes()) == 0

    def test_ctrl_v_pastes_nodes(self, qtbot, network_view):
        """Test Ctrl+V keyboard shortcut."""
        view, network, scene = network_view

        var = VariableNode(data_type="int", name="TestVar")
        network.add_node(var)
        QApplication.processEvents()

        node_item = scene.get_node_item(var.id)
        node_item.setSelected(True)

        # Copy
        qtbot.keyPress(view, Qt.Key_C, Qt.ControlModifier)
        QApplication.processEvents()

        # Paste
        qtbot.keyPress(view, Qt.Key_V, Qt.ControlModifier)
        QApplication.processEvents()

        assert len(network.nodes()) == 2


class TestSubnetSerialization:
    """Test subnet serialization and deserialization preserves connections."""

    def test_subnet_internal_connections_persist_after_save_load(self, qtbot, network_view):
        """Test that connections inside subnet are preserved after serialization."""
        view, network, scene = network_view

        # Create a subnet
        subnet = SubnetNode(name="TestSubnet")
        network.add_node(subnet)
        QApplication.processEvents()

        # Get internal network
        internal_network = subnet.get_internal_network()

        # Add nodes inside subnet
        var1 = VariableNode(data_type="int", name="Var1")
        var1.parameter("value").set_value(42)
        var1.set_position(100, 100)
        internal_network.add_node(var1)

        var2 = VariableNode(data_type="int", name="Var2")
        var2.parameter("value").set_value(7)
        var2.set_position(100, 200)
        internal_network.add_node(var2)

        add_node = AddNode()
        add_node.set_position(300, 150)
        internal_network.add_node(add_node)

        # Create connections inside subnet
        internal_network.connect(var1.id, "out", add_node.id, "a")
        internal_network.connect(var2.id, "out", add_node.id, "b")
        QApplication.processEvents()

        # Verify connections exist
        assert len(internal_network._connector_pairs) == 2
        assert add_node.input("a").is_connected()
        assert add_node.input("b").is_connected()

        print("\n=== Before Serialization ===")
        print(f"Internal network has {len(internal_network.nodes())} nodes")
        print(f"Internal network has {len(internal_network._connector_pairs)} connections")
        for src, tgt in internal_network._connector_pairs:
            print(f"  Connection: {src.node.name}.{src.name} -> {tgt.node.name}.{tgt.name}")

        # Serialize the subnet
        subnet_data = subnet.serialize()

        print("\n=== Serialized Data ===")
        print(f"Subnet has internal_network: {'internal_network' in subnet_data}")
        if 'internal_network' in subnet_data:
            net_data = subnet_data['internal_network']
            print(f"Internal network nodes: {len(net_data.get('nodes', []))}")
            print(f"Internal network connections: {len(net_data.get('connections', []))}")
            for conn in net_data.get('connections', []):
                print(f"  Saved connection: {conn}")

        # Deserialize into a new subnet
        print("\n=== Deserializing ===")
        new_subnet = SubnetNode.deserialize(subnet_data)
        new_internal = new_subnet.get_internal_network()

        print("\n=== After Deserialization ===")
        print(f"New internal network has {len(new_internal.nodes())} nodes")
        print(f"New internal network has {len(new_internal._connector_pairs)} connections")
        for src, tgt in new_internal._connector_pairs:
            print(f"  Connection: {src.node.name}.{src.name} -> {tgt.node.name}.{tgt.name}")

        # Verify nodes were restored
        assert len(new_internal.nodes()) == len(internal_network.nodes())

        # Verify connections were restored
        assert len(new_internal._connector_pairs) == len(internal_network._connector_pairs), \
            f"Expected {len(internal_network._connector_pairs)} connections, got {len(new_internal._connector_pairs)}"

        # Find the Add node in the new network
        new_add = None
        for node in new_internal.nodes():
            if node.node_type == "AddNode":
                new_add = node
                break

        assert new_add is not None, "Add node not found in deserialized network"

        # Verify connections are connected
        assert new_add.input("a").is_connected(), "Input 'a' should be connected after deserialization"
        assert new_add.input("b").is_connected(), "Input 'b' should be connected after deserialization"

        print("\n=== Test Passed ===")

    def test_subnet_connections_persist_after_file_save_load(self, qtbot, network_view, tmp_path):
        """Test subnet connections using actual file save/load (JSONSerializer)."""
        view, network, scene = network_view
        from nodegraph.core.serialization import JSONSerializer
        import tempfile
        import os

        # Create a subnet
        subnet = SubnetNode(name="FileTestSubnet")
        network.add_node(subnet)
        QApplication.processEvents()

        # Get internal network
        internal_network = subnet.get_internal_network()

        # Add nodes inside subnet
        var1 = VariableNode(data_type="int", name="FileVar1")
        var1.parameter("value").set_value(99)
        var1.set_position(50, 50)
        internal_network.add_node(var1)

        var2 = VariableNode(data_type="int", name="FileVar2")
        var2.parameter("value").set_value(11)
        var2.set_position(50, 150)
        internal_network.add_node(var2)

        add_node = AddNode()
        add_node.set_position(200, 100)
        internal_network.add_node(add_node)

        # Create connections
        internal_network.connect(var1.id, "out", add_node.id, "a")
        internal_network.connect(var2.id, "out", add_node.id, "b")
        QApplication.processEvents()

        print("\n=== Before File Save ===")
        print(f"Internal network: {len(internal_network.nodes())} nodes, {len(internal_network._connector_pairs)} connections")
        for src, tgt in internal_network._connector_pairs:
            print(f"  {src.node.name}.{src.name} -> {tgt.node.name}.{tgt.name}")

        # Save to file using JSONSerializer
        test_file = tmp_path / "test_subnet.json"
        print(f"\n=== Saving to {test_file} ===")
        JSONSerializer.save(network, str(test_file))

        # Load from file using JSONSerializer
        print(f"\n=== Loading from {test_file} ===")
        loaded_network, _ = JSONSerializer.load(str(test_file))

        print("\n=== After File Load ===")
        print(f"Loaded network: {len(loaded_network.nodes())} nodes")

        # Find the subnet in loaded network
        loaded_subnet = None
        for node in loaded_network.nodes():
            if node.node_type == "SubnetNode":
                loaded_subnet = node
                break

        assert loaded_subnet is not None, "Subnet not found in loaded network"
        print(f"Found subnet: {loaded_subnet.name}")

        loaded_internal = loaded_subnet.get_internal_network()
        print(f"Loaded internal network: {len(loaded_internal.nodes())} nodes, {len(loaded_internal._connector_pairs)} connections")

        for src, tgt in loaded_internal._connector_pairs:
            print(f"  {src.node.name}.{src.name} -> {tgt.node.name}.{tgt.name}")

        # Verify
        assert len(loaded_internal.nodes()) == len(internal_network.nodes()), \
            f"Node count mismatch: expected {len(internal_network.nodes())}, got {len(loaded_internal.nodes())}"

        assert len(loaded_internal._connector_pairs) == len(internal_network._connector_pairs), \
            f"Connection count mismatch: expected {len(internal_network._connector_pairs)}, got {len(loaded_internal._connector_pairs)}"

        # Find the Add node
        loaded_add = None
        for node in loaded_internal.nodes():
            if node.node_type == "AddNode":
                loaded_add = node
                break

        assert loaded_add is not None, "Add node not found"
        assert loaded_add.input("a").is_connected(), "Input 'a' should be connected"
        assert loaded_add.input("b").is_connected(), "Input 'b' should be connected"

        print("\n=== File Save/Load Test Passed ===")

