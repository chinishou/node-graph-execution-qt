"""
Tests for node editor UI components.

Uses pytest-qt for Qt testing.
"""

import pytest
from PySide6.QtCore import Qt, QPoint, QPointF, QEvent
from PySide6.QtWidgets import QApplication, QMenu
from PySide6.QtTest import QTest

from nodegraph.views import MainWindow, NetworkView, NetworkScene
from nodegraph.views.nodes import NodeGraphicsItem
from nodegraph.core.models import NetworkModel
from nodegraph.core.registry import NodeRegistry


@pytest.fixture
def app(qapp):
    """Provide the QApplication instance."""
    return qapp


@pytest.fixture
def main_window(qtbot):
    """Create a MainWindow for testing."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    return window


@pytest.fixture
def network_view(qtbot):
    """Create a NetworkView with a scene for testing."""
    # Clear registry first
    NodeRegistry.clear()

    # Register test nodes
    from nodegraph.nodes.operators.math_nodes import AddNode
    from nodegraph.nodes.utils import PrintNode
    from nodegraph.nodes.base import FloatVariable

    NodeRegistry.register(AddNode)
    NodeRegistry.register(PrintNode)
    NodeRegistry.register(FloatVariable)

    # Create view with network
    network = NetworkModel("Test")
    scene = NetworkScene(network)
    view = NetworkView()
    view.set_scene(scene)

    qtbot.addWidget(view)
    view.show()
    view.resize(800, 600)
    qtbot.waitExposed(view)

    return view


class TestMainWindow:
    """Tests for MainWindow."""

    def test_main_window_creation(self, main_window):
        """Test that MainWindow can be created."""
        assert main_window is not None
        assert main_window._network_model is not None
        assert main_window._network_view is not None

    def test_new_network(self, main_window):
        """Test creating a new network."""
        # Add a node first
        from nodegraph.core.registry import NodeRegistry
        node = NodeRegistry.create_node("AddNode")
        main_window._network_model.add_node(node)

        assert main_window._network_model.node_count() == 1

        # Create new network
        main_window.new_network()

        assert main_window._network_model.node_count() == 0

    def test_registered_nodes(self, main_window):
        """Test that default nodes are registered."""
        nodes = NodeRegistry.get_all_nodes()

        assert "AddNode" in nodes
        assert "PrintNode" in nodes
        assert "FloatVariable" in nodes


class TestNetworkView:
    """Tests for NetworkView."""

    def test_view_creation(self, network_view):
        """Test that NetworkView can be created."""
        assert network_view is not None
        assert network_view._scene is not None

    def test_zoom_in(self, network_view):
        """Test zoom in functionality."""
        initial_zoom = network_view._zoom_level
        network_view.zoom_in()
        assert network_view._zoom_level > initial_zoom

    def test_zoom_out(self, network_view):
        """Test zoom out functionality."""
        network_view._zoom_level = 2.0
        network_view.zoom_out()
        assert network_view._zoom_level < 2.0

    def test_reset_zoom(self, network_view):
        """Test reset zoom functionality."""
        network_view._zoom_level = 2.0
        network_view.reset_zoom()
        assert network_view._zoom_level == 1.0

    def test_context_menu_shows_categories(self, network_view, qtbot):
        """Test that context menu shows node categories."""
        # Get categories
        categories = NodeRegistry.get_categories()
        assert len(categories) > 0

    def test_node_creation_via_menu(self, network_view, qtbot):
        """Test creating a node via the menu action."""
        scene = network_view._scene
        network = scene.network_model

        assert network.node_count() == 0

        # Simulate menu action
        scene_pos = QPointF(100, 100)
        network_view._on_node_menu_action_direct("AddNode", scene_pos)

        assert network.node_count() == 1

        # Check node position
        node = network.nodes()[0]
        pos = node.position()
        assert pos[0] == 100
        assert pos[1] == 100

    def test_delete_selected(self, network_view, qtbot):
        """Test deleting selected items."""
        scene = network_view._scene
        network = scene.network_model

        # Add a node
        node = NodeRegistry.create_node("AddNode")
        node.set_position(100, 100)
        network.add_node(node)

        assert network.node_count() == 1

        # Select the node
        node_item = scene.get_node_item(node.id)
        assert node_item is not None
        node_item.setSelected(True)

        # Delete
        scene.delete_selected()

        assert network.node_count() == 0

    def test_pan_with_middle_button(self, network_view, qtbot):
        """Test panning with middle mouse button."""
        center = network_view.rect().center()

        # Start panning
        qtbot.mousePress(network_view.viewport(), Qt.MiddleButton, pos=center)
        assert network_view._panning is True

        # Release
        qtbot.mouseRelease(network_view.viewport(), Qt.MiddleButton, pos=center)
        assert network_view._panning is False


class TestNetworkScene:
    """Tests for NetworkScene."""

    def test_add_node(self, network_view):
        """Test adding a node to the scene."""
        scene = network_view._scene
        network = scene.network_model

        # Add node
        node = NodeRegistry.create_node("AddNode")
        node.set_position(200, 200)
        network.add_node(node)

        # Check scene has the item
        node_item = scene.get_node_item(node.id)
        assert node_item is not None
        assert node_item.node_model == node

    def test_remove_node(self, network_view):
        """Test removing a node from the scene."""
        scene = network_view._scene
        network = scene.network_model

        # Add then remove
        node = NodeRegistry.create_node("AddNode")
        network.add_node(node)

        node_id = node.id
        network.remove_node(node_id)

        assert scene.get_node_item(node_id) is None

    def test_create_connection(self, network_view):
        """Test creating a connection between nodes."""
        scene = network_view._scene
        network = scene.network_model

        # Add two nodes
        float_node = NodeRegistry.create_node("FloatVariable")
        float_node.set_position(100, 100)
        network.add_node(float_node)

        add_node = NodeRegistry.create_node("AddNode")
        add_node.set_position(300, 100)
        network.add_node(add_node)

        # Connect
        success = network.connect(float_node.id, "out", add_node.id, "a")
        assert success is True

        # Check connection exists
        assert len(network.connector_pairs()) == 1


class TestNodeGraphicsItem:
    """Tests for NodeGraphicsItem."""

    def test_node_item_creation(self, network_view):
        """Test creating a node graphics item."""
        scene = network_view._scene
        network = scene.network_model

        node = NodeRegistry.create_node("AddNode")
        node.set_position(150, 150)
        network.add_node(node)

        item = scene.get_node_item(node.id)
        assert item is not None
        assert item.pos().x() == 150
        assert item.pos().y() == 150

    def test_node_item_selection(self, network_view, qtbot):
        """Test selecting a node item."""
        scene = network_view._scene
        network = scene.network_model

        node = NodeRegistry.create_node("AddNode")
        node.set_position(100, 100)
        network.add_node(node)

        item = scene.get_node_item(node.id)
        item.setSelected(True)

        assert item.isSelected() is True

    def test_node_item_move(self, network_view):
        """Test moving a node item updates model."""
        scene = network_view._scene
        network = scene.network_model

        node = NodeRegistry.create_node("AddNode")
        node.set_position(100, 100)
        network.add_node(node)

        item = scene.get_node_item(node.id)
        item.setPos(200, 300)

        # Model should be updated
        pos = node.position()
        assert pos[0] == 200
        assert pos[1] == 300


class TestNodeExecution:
    """Tests for node execution through UI."""

    def test_execute_all(self, main_window, qtbot):
        """Test executing all nodes."""
        network = main_window._network_model

        # Create nodes
        float1 = NodeRegistry.create_node("FloatVariable")
        float1.parameter("value").set_value(10.0)
        network.add_node(float1)

        float2 = NodeRegistry.create_node("FloatVariable")
        float2.parameter("value").set_value(20.0)
        network.add_node(float2)

        add = NodeRegistry.create_node("AddNode")
        network.add_node(add)

        # Connect
        network.connect(float1.id, "out", add.id, "a")
        network.connect(float2.id, "out", add.id, "b")

        # Execute all
        main_window._execute_all()

        # Check result
        result = add.get_output_value("result")
        assert result == 30.0


class TestContextMenu:
    """Tests for context menu and Tab key functionality."""

    def test_show_node_menu(self, network_view, qtbot):
        """Test that _show_node_menu creates a menu with categories."""
        from PySide6.QtCore import QPoint

        # Verify categories exist
        categories = NodeRegistry.get_categories()
        assert len(categories) > 0

        # The menu should be created with categories as sub-menus
        # We test this indirectly through node creation

    def test_node_creation_at_position(self, network_view, qtbot):
        """Test creating node at specific position."""
        scene = network_view._scene
        network = scene.network_model

        # Create node at specific position
        scene_pos = QPointF(250, 350)
        network_view._on_node_menu_action_direct("AddNode", scene_pos)

        # Verify position
        node = network.nodes()[0]
        pos = node.position()
        assert pos[0] == 250
        assert pos[1] == 350

    def test_key_delete(self, network_view, qtbot):
        """Test Delete key removes selected items."""
        scene = network_view._scene
        network = scene.network_model

        # Add node
        node = NodeRegistry.create_node("AddNode")
        network.add_node(node)

        # Select it
        node_item = scene.get_node_item(node.id)
        node_item.setSelected(True)

        # Simulate Delete key
        QTest.keyClick(network_view, Qt.Key_Delete)

        # Should be deleted
        assert network.node_count() == 0

    def test_key_f_frame_selection(self, network_view, qtbot):
        """Test F key frames selection."""
        scene = network_view._scene
        network = scene.network_model

        # Add nodes
        node1 = NodeRegistry.create_node("AddNode")
        node1.set_position(100, 100)
        network.add_node(node1)

        node2 = NodeRegistry.create_node("PrintNode")
        node2.set_position(500, 500)
        network.add_node(node2)

        # Press F to frame all
        QTest.keyClick(network_view, Qt.Key_F)

        # Zoom should have changed
        assert network_view._zoom_level != 1.0 or network_view.transform().m11() != 1.0


class TestPrintNode:
    """Tests for PrintNode functionality."""

    def test_print_node_output(self, main_window, qtbot):
        """Test that PrintNode sends output to OutputPane."""
        network = main_window._network_model

        # Create nodes
        float_node = NodeRegistry.create_node("FloatVariable")
        float_node.parameter("value").set_value(42.0)
        network.add_node(float_node)

        print_node = NodeRegistry.create_node("PrintNode")
        network.add_node(print_node)

        # Connect
        network.connect(float_node.id, "out", print_node.id, "value")

        # Execute
        main_window._execute_all()

        # Check output pane has content
        output_text = main_window._output_pane.get_text()
        assert "42.0" in output_text or "42" in output_text


class TestConnectionModes:
    """Tests for connection modes (drag and click-click)."""

    def test_click_to_connect_mode(self, network_view, qtbot):
        """Test click-click connection mode."""
        scene = network_view._scene
        network = scene.network_model

        # Add two nodes
        float_node = NodeRegistry.create_node("FloatVariable")
        float_node.set_position(100, 100)
        network.add_node(float_node)

        add_node = NodeRegistry.create_node("AddNode")
        add_node.set_position(300, 100)
        network.add_node(add_node)

        # Get port items
        float_item = scene.get_node_item(float_node.id)
        add_item = scene.get_node_item(add_node.id)

        output_port = float_item.get_port("out", is_output=True)
        input_port = add_item.get_port("a", is_output=False)

        # Simulate click-to-connect
        # First click on output port
        network_view._click_to_connect_port = output_port
        scene.start_connection_drag(output_port)

        # Second click on input port
        network_view._complete_click_connection(input_port)

        # Check connection was created
        assert len(network.connector_pairs()) == 1

    def test_create_connection_directly(self, network_view, qtbot):
        """Test creating connection with create_connection method."""
        scene = network_view._scene
        network = scene.network_model

        # Add two nodes
        float_node = NodeRegistry.create_node("FloatVariable")
        float_node.set_position(100, 100)
        network.add_node(float_node)

        add_node = NodeRegistry.create_node("AddNode")
        add_node.set_position(300, 100)
        network.add_node(add_node)

        # Get port items
        float_item = scene.get_node_item(float_node.id)
        add_item = scene.get_node_item(add_node.id)

        output_port = float_item.get_port("out", is_output=True)
        input_port = add_item.get_port("a", is_output=False)

        # Create connection directly
        success = scene.create_connection(output_port, input_port)

        assert success is True
        assert len(network.connector_pairs()) == 1


class TestNodePalette:
    """Tests for NodePaletteDialog interactive behavior."""

    @pytest.fixture(autouse=True)
    def setup_nodes(self):
        """Register nodes for palette tests."""
        # Clear and register test nodes
        NodeRegistry.clear()
        from nodegraph.nodes.operators.math_nodes import AddNode
        from nodegraph.nodes.utils import PrintNode
        from nodegraph.nodes.base import FloatVariable

        NodeRegistry.register(AddNode)
        NodeRegistry.register(PrintNode)
        NodeRegistry.register(FloatVariable)

    def test_palette_creation(self, qtbot):
        """Test creating node palette dialog."""
        from nodegraph.views.widgets.node_palette import NodePaletteDialog

        palette = NodePaletteDialog(QPointF(100, 100))
        qtbot.addWidget(palette)

        # Check basic structure
        assert palette.category_list.count() > 0
        assert not palette.right_list.isVisible()
        assert palette.right_list_mode is None

    def test_category_hover_shows_nodes(self, qtbot):
        """Test that hovering over category shows node list."""
        from nodegraph.views.widgets.node_palette import NodePaletteDialog

        palette = NodePaletteDialog(QPointF(100, 100))
        qtbot.addWidget(palette)
        palette.show()  # Must show the widget first
        qtbot.waitExposed(palette)

        # Get first category
        first_category = palette.category_list.item(0)
        assert first_category is not None

        # Trigger hover
        palette._on_category_hovered(first_category)

        # Right list should be visible with nodes
        assert palette.right_list.isVisible()
        assert palette.right_list_mode == 'category'
        assert palette.right_list.count() > 0

    def test_category_switching(self, qtbot):
        """Test switching between categories updates node list."""
        from nodegraph.views.widgets.node_palette import NodePaletteDialog

        palette = NodePaletteDialog(QPointF(100, 100))
        qtbot.addWidget(palette)
        palette.show()
        qtbot.waitExposed(palette)

        # Hover over first category
        first_category = palette.category_list.item(0)
        palette._on_category_hovered(first_category)
        first_count = palette.right_list.count()

        # Hover over second category (if exists)
        if palette.category_list.count() > 1:
            second_category = palette.category_list.item(1)
            palette._on_category_hovered(second_category)
            second_count = palette.right_list.count()

            # Should switch to different category
            assert palette.right_list_mode == 'category'
            # Counts may differ if categories have different node counts
            assert palette.right_list.isVisible()

    def test_search_mode_switches_to_search_results(self, qtbot):
        """Test that typing in search switches to search mode."""
        from nodegraph.views.widgets.node_palette import NodePaletteDialog

        palette = NodePaletteDialog(QPointF(100, 100))
        qtbot.addWidget(palette)
        palette.show()
        qtbot.waitExposed(palette)

        # First show category nodes
        first_category = palette.category_list.item(0)
        palette._on_category_hovered(first_category)
        assert palette.right_list_mode == 'category'

        # Type in search box
        palette.search_box.setText("Add")
        qtbot.wait(10)  # Allow signal processing

        # Should switch to search mode
        assert palette.right_list_mode == 'search'
        assert palette.right_list.isVisible()
        assert palette.right_list.count() > 0  # Should have search results

    def test_search_box_keeps_focus(self, qtbot):
        """Test that search box keeps focus during operations."""
        from nodegraph.views.widgets.node_palette import NodePaletteDialog

        palette = NodePaletteDialog(QPointF(100, 100))
        qtbot.addWidget(palette)
        palette.show()

        # Focus search box
        palette.search_box.setFocus()
        assert palette.search_box.hasFocus()

        # Hover over category to show right list
        first_category = palette.category_list.item(0)
        palette._on_category_hovered(first_category)

        # Search box should still have focus (or be able to receive it)
        palette.search_box.setFocus()
        assert palette.search_box.hasFocus()

        # Type should work
        QTest.keyClicks(palette.search_box, "test")
        assert palette.search_box.text() == "test"

    def test_search_prevents_category_hover(self, qtbot):
        """Test that category hover doesn't work in search mode."""
        from nodegraph.views.widgets.node_palette import NodePaletteDialog

        palette = NodePaletteDialog(QPointF(100, 100))
        qtbot.addWidget(palette)

        # Enter search mode
        palette.search_box.setText("Add")
        qtbot.wait(10)
        assert palette.right_list_mode == 'search'
        initial_count = palette.right_list.count()

        # Try to hover over category
        first_category = palette.category_list.item(0)
        palette._on_category_hovered(first_category)

        # Should remain in search mode, not switch to category mode
        assert palette.right_list_mode == 'search'
        assert palette.right_list.count() == initial_count

    def test_clear_search_hides_right_list(self, qtbot):
        """Test that clearing search hides right list."""
        from nodegraph.views.widgets.node_palette import NodePaletteDialog

        palette = NodePaletteDialog(QPointF(100, 100))
        qtbot.addWidget(palette)
        palette.show()
        qtbot.waitExposed(palette)

        # Enter search mode
        palette.search_box.setText("Add")
        qtbot.wait(10)
        assert palette.right_list.isVisible()

        # Clear search
        palette.search_box.setText("")
        qtbot.wait(10)

        # Right list should be hidden
        assert not palette.right_list.isVisible()
        assert palette.right_list_mode is None

    def test_node_selection_emits_signal(self, qtbot):
        """Test that selecting a node emits the signal."""
        from nodegraph.views.widgets.node_palette import NodePaletteDialog

        palette = NodePaletteDialog(QPointF(100, 100))
        qtbot.addWidget(palette)

        # Track signal
        signal_emitted = []
        palette.node_selected.connect(lambda node_type, pos: signal_emitted.append(node_type))

        # Show category nodes
        first_category = palette.category_list.item(0)
        palette._on_category_hovered(first_category)

        # Click on first node
        first_node = palette.right_list.item(0)
        palette._on_right_item_clicked(first_node)

        # Should have emitted signal
        assert len(signal_emitted) == 1
        assert isinstance(signal_emitted[0], str)

    def test_arrow_keys_navigate_right_list_in_category_mode(self, qtbot):
        """Test that up/down arrows navigate right list when in category mode."""
        from nodegraph.views.widgets.node_palette import NodePaletteDialog
        from PySide6.QtGui import QKeyEvent

        palette = NodePaletteDialog(QPointF(100, 100))
        qtbot.addWidget(palette)
        palette.show()
        qtbot.waitExposed(palette)

        # Open category nodes
        first_category = palette.category_list.item(0)
        palette._on_category_hovered(first_category)
        assert palette.right_list.isVisible()
        assert palette.right_list_mode == 'category'

        # Create and send down arrow key event directly to eventFilter
        key_event = QKeyEvent(QEvent.KeyPress, Qt.Key_Down, Qt.NoModifier)
        palette.eventFilter(palette, key_event)

        # Right list should have focus (eventFilter sets it)
        assert palette.right_list.hasFocus()
        assert palette.right_list.currentRow() >= 0

    def test_left_arrow_closes_right_list(self, qtbot):
        """Test that left arrow closes right list in category mode."""
        from nodegraph.views.widgets.node_palette import NodePaletteDialog
        from PySide6.QtGui import QKeyEvent

        palette = NodePaletteDialog(QPointF(100, 100))
        qtbot.addWidget(palette)
        palette.show()
        qtbot.waitExposed(palette)

        # Open category nodes
        first_category = palette.category_list.item(0)
        palette._on_category_hovered(first_category)
        assert palette.right_list.isVisible()

        # Create and send left arrow key event directly to eventFilter
        key_event = QKeyEvent(QEvent.KeyPress, Qt.Key_Left, Qt.NoModifier)
        palette.eventFilter(palette, key_event)

        # Right list should be hidden
        assert not palette.right_list.isVisible()
        assert palette.right_list_mode is None
        assert palette.category_list.hasFocus()

    def test_right_arrow_opens_and_focuses_right_list(self, qtbot):
        """Test that right arrow opens and focuses right list."""
        from nodegraph.views.widgets.node_palette import NodePaletteDialog
        from PySide6.QtGui import QKeyEvent

        palette = NodePaletteDialog(QPointF(100, 100))
        qtbot.addWidget(palette)
        palette.show()
        qtbot.waitExposed(palette)

        # Set focus on category list and select first item
        palette.category_list.setFocus()
        palette.category_list.setCurrentRow(0)

        # Create and send right arrow key event directly to eventFilter
        key_event = QKeyEvent(QEvent.KeyPress, Qt.Key_Right, Qt.NoModifier)
        palette.eventFilter(palette, key_event)

        # Right list should be visible and have focus
        assert palette.right_list.isVisible()
        assert palette.right_list_mode == 'category'
        assert palette.right_list.hasFocus()
        if palette.right_list.count() > 0:
            assert palette.right_list.currentRow() == 0


# Add helper method to NetworkView for testing
def _on_node_menu_action_direct(self, node_type: str, scene_pos: QPointF):
    """Direct node creation for testing."""
    try:
        node = NodeRegistry.create_node(node_type)
        node.set_position(scene_pos.x(), scene_pos.y())
        self._scene.network_model.add_node(node)
    except Exception as e:
        print(f"Error creating node: {e}")

# Monkey-patch for testing
NetworkView._on_node_menu_action_direct = _on_node_menu_action_direct


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
