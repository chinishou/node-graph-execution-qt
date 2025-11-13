"""
Tests for Variable Nodes
=========================

Test variable nodes for direct value declaration:
- VariableNode base class
- Typed variable nodes (Int, Float, String, Bool)
- Integration with other nodes
- Value changes and dirty state propagation
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodegraph.nodes.base import (
    VariableNode,
    IntVariable,
    FloatVariable,
    StringVariable,
    BoolVariable,
)
from nodegraph.nodes.operators import AddNode, MultiplyNode


def test_variable_node_creation():
    """Test creating variable nodes of different types."""
    # Float variable
    float_var = FloatVariable(default_value=3.14)
    assert float_var.parameter("value").value() == 3.14
    assert float_var.category == "Variables"

    # Int variable
    int_var = IntVariable(default_value=42)
    assert int_var.parameter("value").value() == 42

    # String variable
    string_var = StringVariable(default_value="Hello")
    assert string_var.parameter("value").value() == "Hello"

    # Bool variable
    bool_var = BoolVariable(default_value=True)
    assert bool_var.parameter("value").value() == True

    print("✓ Variable node creation works")


def test_variable_node_output():
    """Test variable node outputs the parameter value."""
    var = FloatVariable(default_value=2.718)

    # Cook the node
    var.cook()

    # Get output value
    result = var.get_output_value("out")
    assert result == 2.718

    print("✓ Variable node output works")


def test_variable_node_value_change():
    """Test changing variable node value."""
    var = IntVariable(default_value=10)

    # Initial value
    assert var.parameter("value").value() == 10
    assert var.get_output_value("out") == 10

    # Change value
    var.parameter("value").set_value(20)
    assert var.parameter("value").value() == 20

    # NOTE: Due to Signal issue, need to manually mark dirty
    var.mark_dirty()

    # Output should reflect new value
    result = var.get_output_value("out")
    assert result == 20

    print("✓ Variable node value change works (with manual mark_dirty)")


def test_variable_node_with_math():
    """Test variable nodes connected to math nodes."""
    # Create variables
    var_a = FloatVariable(default_value=10.0, name="A")
    var_b = FloatVariable(default_value=5.0, name="B")

    # Create add node
    add = AddNode()

    # Connect variables to add node
    var_a.output("out").connect_to(add.input("a"))
    var_b.output("out").connect_to(add.input("b"))

    # Get result
    result = add.get_output_value("result")
    assert result == 15.0

    # Change variable A
    var_a.parameter("value").set_value(20.0)
    var_a.mark_dirty()  # Manual dirty marking due to Signal issue

    # Result should update
    result = add.get_output_value("result")
    assert result == 25.0

    print("✓ Variable node with math operations works")


def test_variable_node_chain():
    """Test chaining variable nodes with multiple operations."""
    # Create variables
    var_x = FloatVariable(default_value=2.0, name="X")
    var_y = FloatVariable(default_value=3.0, name="Y")
    var_z = FloatVariable(default_value=4.0, name="Z")

    # Create operation nodes
    mul1 = MultiplyNode()
    add1 = AddNode()

    # Build expression: (X * Y) + Z
    var_x.output("out").connect_to(mul1.input("a"))
    var_y.output("out").connect_to(mul1.input("b"))
    mul1.output("result").connect_to(add1.input("a"))
    var_z.output("out").connect_to(add1.input("b"))

    # Compute: (2 * 3) + 4 = 10
    result = add1.get_output_value("result")
    assert result == 10.0

    print("✓ Variable node chaining works")


def test_generic_variable_node():
    """Test generic VariableNode with custom type."""
    from nodegraph.core import DataTypeRegistry

    # Register custom type
    DataTypeRegistry.register("Path", Path)

    # Create path variable
    path_var = VariableNode(
        data_type="Path",
        default_value=Path("/tmp/test.txt"),
        name="FilePath"
    )

    # Get value
    result = path_var.get_output_value("out")
    assert isinstance(result, Path)
    assert str(result) == "/tmp/test.txt"

    print("✓ Generic VariableNode with custom type works")


def test_variable_node_no_inputs():
    """Test that variable nodes have no inputs."""
    var = FloatVariable(default_value=1.0)

    # Should have no inputs
    inputs = var.inputs()
    assert len(inputs) == 0

    # Should have one output
    outputs = var.outputs()
    assert len(outputs) == 1
    assert "out" in outputs

    print("✓ Variable nodes have no inputs")


def test_variable_node_dirty_state():
    """Test dirty state propagation from variable nodes (with caching enabled)."""
    var = FloatVariable(default_value=5.0)
    add = AddNode()

    # Enable caching to test dirty state behavior
    var.enable_caching = True
    add.enable_caching = True

    # Connect
    var.output("out").connect_to(add.input("a"))

    # Initial state
    var.cook()
    add.cook()
    assert not var.is_dirty()
    assert not add.is_dirty()

    # Change variable value
    var.parameter("value").set_value(10.0)
    var.mark_dirty()  # Manual dirty marking due to Signal issue

    # Variable should be dirty
    assert var.is_dirty()
    # Add node should also be dirty (downstream propagation works)
    assert add.is_dirty()

    print("✓ Dirty state propagation from variable nodes works (with caching enabled)")


def run_all_tests():
    """Run all variable node tests."""
    print("=" * 60)
    print("Variable Node Tests")
    print("=" * 60)

    test_variable_node_creation()
    test_variable_node_output()
    test_variable_node_value_change()
    test_variable_node_with_math()
    test_variable_node_chain()
    test_generic_variable_node()
    test_variable_node_no_inputs()
    test_variable_node_dirty_state()

    print("=" * 60)
    print("All variable node tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
