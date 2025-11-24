"""
Tests for UI Nodes
==================

Comprehensive tests for UI preview system nodes including:
- Basic node creation and execution
- Dynamic input control (num_children parameter)
- Connection handling with dynamic inputs
- Widget lifecycle management
"""

import pytest
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QMainWindow

from nodegraph.core.models import NetworkModel
from nodegraph.core.registry import NodeRegistry
from nodegraph.nodes.ui import (
    UIRootNode,
    LabelNode,
    ButtonNode,
    VBoxLayoutNode,
    HBoxLayoutNode,
    QWidgetContainerNode,
    QMainWindowNode,
)


@pytest.fixture(autouse=True)
def register_ui_nodes():
    """Register UI nodes for testing."""
    NodeRegistry.register(UIRootNode)
    NodeRegistry.register(LabelNode)
    NodeRegistry.register(ButtonNode)
    NodeRegistry.register(VBoxLayoutNode)
    NodeRegistry.register(HBoxLayoutNode)
    NodeRegistry.register(QWidgetContainerNode)
    NodeRegistry.register(QMainWindowNode)
    yield
    # Cleanup after tests
    NodeRegistry.reset()


@pytest.fixture
def network():
    """Create a test network."""
    return NetworkModel("/test")


class TestBasicUINodes:
    """Test basic UI node functionality."""

    def test_ui_root_node_creation(self, network):
        """Test UIRootNode can be created."""
        root = UIRootNode()
        network.add_node(root)

        assert root.node_type == "UIRootNode"
        assert root.has_input("widget")
        assert root.has_output("widget")

    def test_label_node_creation(self, network):
        """Test LabelNode can be created and executed."""
        label = LabelNode()
        network.add_node(label)

        # Set parameters
        label.parameter("text").set_value("Test Label")
        label.parameter("alignment").set_value("center")

        # Execute
        success = label.execute()
        assert success is True

        # Check output
        widget = label.get_output_value("widget")
        assert isinstance(widget, QLabel)
        assert widget.text() == "Test Label"

    def test_button_node_creation(self, network):
        """Test ButtonNode can be created and executed."""
        button = ButtonNode()
        network.add_node(button)

        # Set parameters
        button.parameter("text").set_value("Click Me")
        button.parameter("width").set_value(150)
        button.parameter("height").set_value(40)

        # Execute
        success = button.execute()
        assert success is True

        # Check output
        widget = button.get_output_value("widget")
        assert isinstance(widget, QPushButton)
        assert widget.text() == "Click Me"
        assert widget.minimumWidth() == 150
        assert widget.minimumHeight() == 40


class TestDynamicInputControl:
    """Test dynamic input control with num_children parameter."""

    def test_vbox_default_children(self, network):
        """Test VBoxLayoutNode has default number of children."""
        layout = VBoxLayoutNode()
        network.add_node(layout)

        # Default should be 5 children
        assert layout.parameter("num_children").value() == 5
        assert layout.has_input("child1")
        assert layout.has_input("child5")
        assert not layout.has_input("child6")

    def test_vbox_custom_children_count(self, network):
        """Test VBoxLayoutNode with custom num_children."""
        # Create with 3 children
        layout = VBoxLayoutNode(num_children=3)
        network.add_node(layout)

        assert layout.parameter("num_children").value() == 3
        assert layout.has_input("child1")
        assert layout.has_input("child2")
        assert layout.has_input("child3")
        assert not layout.has_input("child4")

    def test_vbox_with_10_children(self, network):
        """Test VBoxLayoutNode can handle many children."""
        layout = VBoxLayoutNode(num_children=10)
        network.add_node(layout)

        assert layout.parameter("num_children").value() == 10
        for i in range(1, 11):
            assert layout.has_input(f"child{i}")
        assert not layout.has_input("child11")

    def test_hbox_dynamic_children(self, network):
        """Test HBoxLayoutNode dynamic children."""
        layout = HBoxLayoutNode(num_children=7)
        network.add_node(layout)

        assert layout.parameter("num_children").value() == 7
        for i in range(1, 8):
            assert layout.has_input(f"child{i}")


class TestConnectionsWithDynamicInputs:
    """Test connections behavior with dynamic inputs."""

    def test_connect_to_dynamic_inputs(self, network):
        """Test connecting widgets to layout with dynamic inputs."""
        # Create nodes
        label1 = LabelNode()
        label2 = LabelNode()
        label3 = LabelNode()
        layout = VBoxLayoutNode(num_children=3)

        network.add_node(label1)
        network.add_node(label2)
        network.add_node(label3)
        network.add_node(layout)

        # Connect all labels to layout
        network.connect(label1.id, "widget", layout.id, "child1")
        network.connect(label2.id, "widget", layout.id, "child2")
        network.connect(label3.id, "widget", layout.id, "child3")

        # Verify connections
        assert layout.input("child1").is_connected()
        assert layout.input("child2").is_connected()
        assert layout.input("child3").is_connected()

        # Execute layout
        success = layout.execute()
        assert success is True

        # Check output widget
        container = layout.get_output_value("widget")
        assert isinstance(container, QWidget)
        assert container.layout() is not None

    def test_partial_connections(self, network):
        """Test layout works with partial connections."""
        label1 = LabelNode()
        layout = VBoxLayoutNode(num_children=5)

        network.add_node(label1)
        network.add_node(layout)

        # Only connect to child1, leave others empty
        network.connect(label1.id, "widget", layout.id, "child1")

        # Should still execute successfully
        success = layout.execute()
        assert success is True

        container = layout.get_output_value("widget")
        assert isinstance(container, QWidget)

    def test_connections_beyond_num_children(self, network):
        """Test that inputs beyond num_children don't exist."""
        label = LabelNode()
        layout = VBoxLayoutNode(num_children=3)

        network.add_node(label)
        network.add_node(layout)

        # Try to connect to child4 (doesn't exist)
        with pytest.raises((KeyError, AttributeError, Exception)):
            network.connect(label.id, "widget", layout.id, "child4")


class TestParameterChangeScenarios:
    """Test scenarios when num_children parameter changes."""

    def test_num_children_parameter_exists(self, network):
        """Test that num_children parameter is accessible."""
        layout = VBoxLayoutNode(num_children=5)
        network.add_node(layout)

        num_children_param = layout.parameter("num_children")
        assert num_children_param is not None
        assert num_children_param.value() == 5

    def test_read_num_children_in_compute(self, network):
        """Test that compute reads current num_children value."""
        layout = VBoxLayoutNode(num_children=3)
        network.add_node(layout)

        # Create some labels
        labels = [LabelNode() for _ in range(3)]
        for i, label in enumerate(labels, 1):
            network.add_node(label)
            label.parameter("text").set_value(f"Label {i}")
            network.connect(label.id, "widget", layout.id, f"child{i}")

        # Execute - should handle 3 children
        success = layout.execute()
        assert success is True

        container = layout.get_output_value("widget")
        # Should have 3 widgets in layout (plus stretch)
        assert container.layout().count() == 4  # 3 widgets + 1 stretch


class TestLayoutNodeComputation:
    """Test layout node computation and widget creation."""

    def test_vbox_layout_computation(self, network):
        """Test VBoxLayoutNode creates proper layout."""
        label1 = LabelNode()
        label2 = LabelNode()
        layout = VBoxLayoutNode(num_children=2)

        network.add_node(label1)
        network.add_node(label2)
        network.add_node(layout)

        label1.parameter("text").set_value("First")
        label2.parameter("text").set_value("Second")

        network.connect(label1.id, "widget", layout.id, "child1")
        network.connect(label2.id, "widget", layout.id, "child2")

        # Execute
        layout.execute()

        container = layout.get_output_value("widget")
        assert container.layout() is not None
        assert container.layout().count() == 3  # 2 labels + stretch

    def test_hbox_layout_computation(self, network):
        """Test HBoxLayoutNode creates horizontal layout."""
        button1 = ButtonNode()
        button2 = ButtonNode()
        layout = HBoxLayoutNode(num_children=2)

        network.add_node(button1)
        network.add_node(button2)
        network.add_node(layout)

        button1.parameter("text").set_value("Left")
        button2.parameter("text").set_value("Right")

        network.connect(button1.id, "widget", layout.id, "child1")
        network.connect(button2.id, "widget", layout.id, "child2")

        # Execute
        layout.execute()

        container = layout.get_output_value("widget")
        assert container.layout() is not None

    def test_layout_spacing_and_margins(self, network):
        """Test layout spacing and margins parameters."""
        layout = VBoxLayoutNode(num_children=1)
        network.add_node(layout)

        layout.parameter("spacing").set_value(15)
        layout.parameter("margins").set_value(20)

        layout.execute()

        container = layout.get_output_value("widget")
        assert container.layout().spacing() == 15


class TestContainerNodes:
    """Test container nodes (QWidget, QMainWindow)."""

    def test_qwidget_container_vbox(self, network):
        """Test QWidgetContainerNode with vbox layout."""
        label = LabelNode()
        container = QWidgetContainerNode(num_children=2)

        network.add_node(label)
        network.add_node(container)

        container.parameter("layout_type").set_value("vbox")
        network.connect(label.id, "widget", container.id, "child1")

        container.execute()

        widget = container.get_output_value("widget")
        assert isinstance(widget, QWidget)

    def test_qwidget_container_hbox(self, network):
        """Test QWidgetContainerNode with hbox layout."""
        container = QWidgetContainerNode(num_children=3)
        network.add_node(container)

        container.parameter("layout_type").set_value("hbox")
        container.execute()

        widget = container.get_output_value("widget")
        assert isinstance(widget, QWidget)

    def test_qmainwindow_node(self, network):
        """Test QMainWindowNode."""
        label = LabelNode()
        main_window = QMainWindowNode()

        network.add_node(label)
        network.add_node(main_window)

        main_window.parameter("title").set_value("Test Window")
        main_window.parameter("width").set_value(1024)
        main_window.parameter("height").set_value(768)

        network.connect(label.id, "widget", main_window.id, "central_widget")

        main_window.execute()

        window = main_window.get_output_value("widget")
        assert isinstance(window, QMainWindow)
        assert window.windowTitle() == "Test Window"
        assert window.width() == 1024
        assert window.height() == 768


class TestComplexUIHierarchy:
    """Test complex UI hierarchies."""

    def test_nested_layouts(self, network):
        """Test nested layout structure."""
        # Create structure: VBox[ Label, HBox[Button1, Button2] ]
        label = LabelNode()
        button1 = ButtonNode()
        button2 = ButtonNode()
        hbox = HBoxLayoutNode(num_children=2)
        vbox = VBoxLayoutNode(num_children=2)

        for node in [label, button1, button2, hbox, vbox]:
            network.add_node(node)

        # Connect buttons to hbox
        network.connect(button1.id, "widget", hbox.id, "child1")
        network.connect(button2.id, "widget", hbox.id, "child2")

        # Connect label and hbox to vbox
        network.connect(label.id, "widget", vbox.id, "child1")
        network.connect(hbox.id, "widget", vbox.id, "child2")

        # Execute entire hierarchy
        vbox.execute()

        container = vbox.get_output_value("widget")
        assert isinstance(container, QWidget)
        assert container.layout() is not None

    def test_ui_root_integration(self, network):
        """Test UIRootNode with complete UI."""
        label = LabelNode()
        button = ButtonNode()
        layout = VBoxLayoutNode(num_children=2)
        root = UIRootNode()

        for node in [label, button, layout, root]:
            network.add_node(node)

        label.parameter("text").set_value("Welcome")
        button.parameter("text").set_value("Start")

        # Build hierarchy
        network.connect(label.id, "widget", layout.id, "child1")
        network.connect(button.id, "widget", layout.id, "child2")
        network.connect(layout.id, "widget", root.id, "widget")

        # Execute root
        root.execute()

        result_widget = root.get_output_value("widget")
        assert isinstance(result_widget, QWidget)


class TestWidgetLifecycle:
    """Test widget lifecycle with multiple refreshes."""

    def test_multiple_executions(self, network):
        """Test that nodes can be executed multiple times safely."""
        label = LabelNode()
        network.add_node(label)

        label.parameter("text").set_value("First")

        # First execution
        label.execute()
        widget1 = label.get_output_value("widget")
        assert isinstance(widget1, QLabel)
        assert widget1.text() == "First"

        # Change parameter and execute again
        label.parameter("text").set_value("Second")
        label.execute()
        widget2 = label.get_output_value("widget")
        assert isinstance(widget2, QLabel)
        assert widget2.text() == "Second"

        # Widgets should be different instances
        assert widget1 is not widget2

    def test_layout_multiple_executions(self, network):
        """Test layout can be executed multiple times."""
        label = LabelNode()
        layout = VBoxLayoutNode(num_children=1)

        network.add_node(label)
        network.add_node(layout)

        network.connect(label.id, "widget", layout.id, "child1")

        # Execute multiple times
        for i in range(3):
            label.parameter("text").set_value(f"Iteration {i}")
            layout.execute()
            container = layout.get_output_value("widget")
            assert isinstance(container, QWidget)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_layout(self, network):
        """Test layout with no children connected."""
        layout = VBoxLayoutNode(num_children=5)
        network.add_node(layout)

        # Execute without any connections
        success = layout.execute()
        assert success is True

        container = layout.get_output_value("widget")
        assert isinstance(container, QWidget)

    def test_zero_children(self, network):
        """Test layout with zero children."""
        layout = VBoxLayoutNode(num_children=0)
        network.add_node(layout)

        success = layout.execute()
        assert success is True

    def test_large_number_of_children(self, network):
        """Test layout with large number of children."""
        layout = VBoxLayoutNode(num_children=50)
        network.add_node(layout)

        # Create and connect 50 labels
        labels = [LabelNode() for _ in range(50)]
        for i, label in enumerate(labels, 1):
            network.add_node(label)
            label.parameter("text").set_value(f"Label {i}")
            network.connect(label.id, "widget", layout.id, f"child{i}")

        success = layout.execute()
        assert success is True

        container = layout.get_output_value("widget")
        # 50 labels + 1 stretch
        assert container.layout().count() == 51
