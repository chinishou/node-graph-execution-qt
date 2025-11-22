"""
Tests for ParametersPane UI Component
=======================================

Test the parameters pane widget functionality:
- Node display and parameter editing
- Input default value widgets
- Parameter widgets (including dropdowns)
- Output displays
- Connection state handling
- Execute button functionality
"""

import pytest
from PySide6.QtWidgets import QSpinBox, QDoubleSpinBox, QCheckBox, QLineEdit, QLabel, QComboBox
from PySide6.QtCore import Qt

from nodegraph.views.widgets.parameters_pane import ParametersPane
from nodegraph.nodes.base import FloatVariable, IntVariable, BoolVariable, StringVariable
from nodegraph.nodes.operators.math_nodes import AddNode
from nodegraph.nodes.operators.convert_node import ConvertNode
from nodegraph.nodes.utils.output_nodes import PrintNode


@pytest.fixture
def params_pane(qtbot):
    """Create a ParametersPane for testing."""
    pane = ParametersPane()
    qtbot.addWidget(pane)
    pane.show()
    qtbot.waitExposed(pane)
    return pane


class TestParametersPaneCreation:
    """Tests for ParametersPane creation and basic setup."""

    def test_pane_creation(self, params_pane):
        """Test that ParametersPane can be created."""
        assert params_pane is not None
        assert params_pane._header_label.text() == "No Selection"
        assert not params_pane._execute_btn.isEnabled()

    def test_pane_no_node_state(self, params_pane):
        """Test pane state with no node selected."""
        params_pane.set_node(None)
        assert params_pane._header_label.text() == "No Selection"
        assert not params_pane._execute_btn.isEnabled()
        assert len(params_pane._widgets) == 0


class TestParametersPaneNodeDisplay:
    """Tests for displaying nodes in the parameters pane."""

    def test_display_float_variable(self, params_pane):
        """Test displaying a float variable node."""
        node = FloatVariable(default_value=3.14)
        node.name = "MyFloat"

        params_pane.set_node(node)

        assert "MyFloat (FloatVariable)" in params_pane._header_label.text()
        assert params_pane._execute_btn.isEnabled()
        # Should have parameter widget for 'value'
        assert "param_value" in params_pane._widgets

    def test_display_int_variable(self, params_pane):
        """Test displaying an int variable node."""
        node = IntVariable(default_value=42)

        params_pane.set_node(node)

        assert "IntVariable" in params_pane._header_label.text()
        # Parameter widget should be QSpinBox for int type
        widget = params_pane._widgets.get("param_value")
        assert isinstance(widget, QSpinBox)
        assert widget.value() == 42

    def test_display_bool_variable(self, params_pane):
        """Test displaying a bool variable node."""
        node = BoolVariable(default_value=True)

        params_pane.set_node(node)

        # Parameter widget should be QCheckBox for bool type
        widget = params_pane._widgets.get("param_value")
        assert isinstance(widget, QCheckBox)
        assert widget.isChecked()

    def test_display_string_variable(self, params_pane):
        """Test displaying a string variable node."""
        node = StringVariable(default_value="Hello")

        params_pane.set_node(node)

        # Parameter widget should be QLineEdit for str type
        widget = params_pane._widgets.get("param_value")
        assert isinstance(widget, QLineEdit)
        assert widget.text() == "Hello"

    def test_display_add_node(self, params_pane):
        """Test displaying an AddNode with inputs and outputs."""
        node = AddNode()

        params_pane.set_node(node)

        assert "AddNode" in params_pane._header_label.text()
        # Should have input widgets for 'a' and 'b'
        assert "input_a" in params_pane._widgets
        assert "input_b" in params_pane._widgets
        # Should have output display for 'result'
        assert "output_result" in params_pane._widgets

    def test_display_convert_node_with_menu(self, params_pane):
        """Test displaying ConvertNode with dropdown menu parameter."""
        node = ConvertNode()

        params_pane.set_node(node)

        # Should have parameter widget with dropdown (QComboBox) for output_type
        widget = params_pane._widgets.get("param_output_type")
        assert isinstance(widget, QComboBox)
        # Should have menu items: int, float, bool, str
        assert widget.count() == 4


class TestParametersPaneEditing:
    """Tests for editing parameters through the pane."""

    def test_edit_int_parameter(self, params_pane, qtbot):
        """Test editing an int parameter."""
        node = IntVariable(default_value=10)
        params_pane.set_node(node)

        widget = params_pane._widgets.get("param_value")
        assert isinstance(widget, QSpinBox)

        # Change value
        widget.setValue(42)
        qtbot.wait(10)

        # Check parameter was updated
        assert node.parameter("value").value() == 42

    def test_edit_float_parameter(self, params_pane, qtbot):
        """Test editing a float parameter."""
        node = FloatVariable(default_value=1.0)
        params_pane.set_node(node)

        widget = params_pane._widgets.get("param_value")
        assert isinstance(widget, QDoubleSpinBox)

        # Change value
        widget.setValue(3.14)
        qtbot.wait(10)

        # Check parameter was updated
        assert node.parameter("value").value() == 3.14

    def test_edit_bool_parameter(self, params_pane, qtbot):
        """Test editing a bool parameter."""
        node = BoolVariable(default_value=False)
        params_pane.set_node(node)

        widget = params_pane._widgets.get("param_value")
        assert isinstance(widget, QCheckBox)

        # Change value
        widget.setChecked(True)
        qtbot.wait(10)

        # Check parameter was updated
        assert node.parameter("value").value() is True

    def test_edit_string_parameter(self, params_pane, qtbot):
        """Test editing a string parameter."""
        node = StringVariable(default_value="Hello")
        params_pane.set_node(node)

        widget = params_pane._widgets.get("param_value")
        assert isinstance(widget, QLineEdit)

        # Change value
        widget.setText("World")
        qtbot.wait(10)

        # Check parameter was updated
        assert node.parameter("value").value() == "World"

    def test_edit_input_default_value(self, params_pane, qtbot):
        """Test editing an input default value."""
        node = AddNode()
        params_pane.set_node(node)

        widget = params_pane._widgets.get("input_a")
        assert isinstance(widget, QDoubleSpinBox)

        # Change default value
        widget.setValue(5.0)
        qtbot.wait(10)

        # Check input default value was updated
        assert node.input("a").default_value == 5.0

    def test_edit_dropdown_parameter(self, params_pane, qtbot):
        """Test editing a dropdown parameter."""
        node = ConvertNode()
        params_pane.set_node(node)

        widget = params_pane._widgets.get("param_output_type")
        assert isinstance(widget, QComboBox)

        # Change selection
        widget.setCurrentText("int")
        qtbot.wait(10)

        # Check parameter was updated
        assert node.parameter("output_type").value() == "int"

    def test_parameter_changed_signal(self, params_pane, qtbot):
        """Test that parameter_changed signal is emitted."""
        node = FloatVariable(default_value=1.0)
        params_pane.set_node(node)

        signal_emitted = []
        params_pane.parameter_changed.connect(lambda: signal_emitted.append(True))

        widget = params_pane._widgets.get("param_value")
        widget.setValue(2.0)
        qtbot.wait(10)

        assert len(signal_emitted) == 1


class TestParametersPaneConnections:
    """Tests for connection state handling."""

    def test_input_disabled_when_connected(self, params_pane, qtbot):
        """Test that input widgets are disabled when connected."""
        var = FloatVariable(default_value=10.0)
        add_node = AddNode()

        # Connect variable to add node
        var.output("out").connect_to(add_node.input("a"))

        # Display add node in pane
        params_pane.set_node(add_node)

        # Input 'a' widget should be disabled (connected)
        widget_a = params_pane._widgets.get("input_a")
        assert not widget_a.isEnabled()

        # Input 'b' widget should be enabled (not connected)
        widget_b = params_pane._widgets.get("input_b")
        assert widget_b.isEnabled()

    def test_input_enabled_when_disconnected(self, params_pane, qtbot):
        """Test that input widgets are enabled when disconnected."""
        var = FloatVariable(default_value=10.0)
        add_node = AddNode()

        # Connect then disconnect
        var.output("out").connect_to(add_node.input("a"))
        params_pane.set_node(add_node)

        # Should be disabled initially
        widget_a = params_pane._widgets.get("input_a")
        assert not widget_a.isEnabled()

        # Disconnect
        var.output("out").disconnect_from(add_node.input("a"))
        qtbot.wait(10)

        # Should be enabled now
        assert widget_a.isEnabled()

    def test_input_styling_when_connected(self, params_pane, qtbot):
        """Test that input widgets are styled differently when connected."""
        var = FloatVariable(default_value=10.0)
        add_node = AddNode()

        # Display add node first
        params_pane.set_node(add_node)
        widget_a = params_pane._widgets.get("input_a")
        label_a = params_pane._labels.get("input_a")

        # Initial state - enabled and normal styling
        assert widget_a.isEnabled()
        normal_label_style = label_a.styleSheet()

        # Connect
        var.output("out").connect_to(add_node.input("a"))
        qtbot.wait(10)

        # Should have different styling
        assert not widget_a.isEnabled()
        assert label_a.styleSheet() != normal_label_style


class TestParametersPaneExecution:
    """Tests for execute button functionality."""

    def test_execute_button_enabled_with_node(self, params_pane):
        """Test that execute button is enabled when node is set."""
        node = FloatVariable(default_value=1.0)
        params_pane.set_node(node)

        assert params_pane._execute_btn.isEnabled()

    def test_execute_button_disabled_without_node(self, params_pane):
        """Test that execute button is disabled when no node is set."""
        params_pane.set_node(None)

        assert not params_pane._execute_btn.isEnabled()

    def test_execute_button_runs_node(self, params_pane, qtbot):
        """Test that clicking execute button runs the node."""
        node = FloatVariable(default_value=3.14)
        params_pane.set_node(node)

        # Click execute button
        params_pane._execute_btn.click()
        qtbot.wait(10)

        # Node should have output value
        result = node.get_output_value("out")
        assert result == 3.14

    def test_execute_updates_output_displays(self, params_pane, qtbot):
        """Test that executing updates output displays."""
        node = FloatVariable(default_value=42.0)
        params_pane.set_node(node)

        # Initial output display should show "--"
        output_widget = params_pane._widgets.get("output_out")
        assert isinstance(output_widget, QLabel)
        assert output_widget.text() == "--"

        # Execute
        params_pane._execute_btn.click()
        qtbot.wait(10)

        # Output display should show value
        assert "42" in output_widget.text()

    def test_execute_with_connected_nodes(self, params_pane, qtbot):
        """Test executing a node with connections."""
        var_a = FloatVariable(default_value=10.0)
        var_b = FloatVariable(default_value=5.0)
        add_node = AddNode()

        var_a.output("out").connect_to(add_node.input("a"))
        var_b.output("out").connect_to(add_node.input("b"))

        params_pane.set_node(add_node)

        # Execute (should execute dependencies too)
        params_pane._execute_btn.click()
        qtbot.wait(10)

        # Output should show sum
        output_widget = params_pane._widgets.get("output_result")
        assert "15" in output_widget.text()


class TestParametersPaneRefresh:
    """Tests for pane refresh functionality."""

    def test_refresh_with_node(self, params_pane):
        """Test refreshing the pane with a node."""
        node = FloatVariable(default_value=1.0)
        params_pane.set_node(node)

        # Modify node
        node.parameter("value").set_value(2.0)

        # Refresh
        params_pane.refresh()

        # Widget should show new value
        widget = params_pane._widgets.get("param_value")
        assert widget.value() == 2.0

    def test_switching_nodes(self, params_pane):
        """Test switching between different nodes."""
        node1 = FloatVariable(default_value=1.0)
        node2 = IntVariable(default_value=42)

        # Set first node
        params_pane.set_node(node1)
        assert "FloatVariable" in params_pane._header_label.text()

        # Switch to second node
        params_pane.set_node(node2)
        assert "IntVariable" in params_pane._header_label.text()

        # Widgets should be for second node
        widget = params_pane._widgets.get("param_value")
        assert isinstance(widget, QSpinBox)
        assert widget.value() == 42


def run_all_tests():
    """Run all parameters pane tests."""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_all_tests()
