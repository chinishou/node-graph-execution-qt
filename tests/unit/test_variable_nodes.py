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
    var.cook()
    assert var.get_output_value("out") == 10

    # Change value
    var.parameter("value").set_value(20)
    assert var.parameter("value").value() == 20

    # Cook again to compute new value
    var.cook()

    # Output should reflect new value
    result = var.get_output_value("out")
    assert result == 20

    print("✓ Variable node value change works")


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

    # Cook and get result
    var_a.cook()
    var_b.cook()
    add.cook()
    result = add.get_output_value("result")
    assert result == 15.0

    # Change variable A
    var_a.parameter("value").set_value(20.0)

    # Cook again to recompute
    var_a.cook()
    add.cook()

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

    # Compute: (2 * 3) + 4 = 10 - cook in topological order
    var_x.cook()
    var_y.cook()
    var_z.cook()
    mul1.cook()
    add1.cook()
    result = add1.get_output_value("result")
    assert result == 10.0

    print("✓ Variable node chaining works")


def test_generic_variable_node():
    """Test generic VariableNode with custom type."""
    from nodegraph.core import DataTypeRegistry
    import tempfile
    import os

    # Register custom type
    DataTypeRegistry.register("Path", Path)

    # Use a cross-platform temp path
    temp_dir = tempfile.gettempdir()
    test_path = Path(temp_dir) / "test.txt"

    # Create path variable
    path_var = VariableNode(
        data_type="Path",
        default_value=test_path,
        name="FilePath"
    )

    # Cook and get value
    path_var.cook()
    result = path_var.get_output_value("out")
    assert isinstance(result, Path)
    # Verify the path matches
    assert result == test_path

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


# NOTE: test_variable_node_dirty_state removed - dirty state functionality
# was removed in favor of always-execute-from-scratch design


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

    print("=" * 60)
    print("All variable node tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
