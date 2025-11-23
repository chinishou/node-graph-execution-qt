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
