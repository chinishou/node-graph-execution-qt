"""
Test New Features
=================

This example demonstrates all the newly implemented features:
1. DataTypeRegistry with ordered menu and custom types
2. VariableNode for direct value declaration
3. Multi-connection inputs with MergeNode
4. Dataclass-based models (simpler serialization)
5. Type conversion support
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodegraph.core import DataTypeRegistry
from nodegraph.nodes.base import FloatVariable, IntVariable, StringVariable, BoolVariable, VariableNode
from nodegraph.nodes.operators import AddNode, MultiplyNode
from nodegraph.nodes.utils import MergeNode, TypedMergeNode


def test_data_type_registry():
    """Test DataTypeRegistry features."""
    print("=" * 60)
    print("Testing DataTypeRegistry")
    print("=" * 60)

    # Get ordered types (built-in ordered menu)
    types = DataTypeRegistry.get_ordered_types()
    print(f"Built-in types (ordered): {types}")

    # Register custom type
    DataTypeRegistry.register("Path", Path, description="File system path")
    print(f"\nRegistered custom type 'Path'")

    # Get updated types list
    types = DataTypeRegistry.get_ordered_types()
    print(f"All types after custom registration: {types}")

    # Test type conversion
    print(f"\nType conversions:")
    print(f"  int(3.14) -> {DataTypeRegistry.convert(3.14, 'int')}")
    print(f"  float('3.14') -> {DataTypeRegistry.convert('3.14', 'float')}")
    print(f"  str(42) -> {DataTypeRegistry.convert(42, 'str')}")
    print(f"  bool(1) -> {DataTypeRegistry.convert(1, 'bool')}")

    # Test type compatibility
    print(f"\nType compatibility:")
    print(f"  can_convert('int', 'float') -> {DataTypeRegistry.can_convert('int', 'float')}")
    print(f"  can_convert('str', 'int') -> {DataTypeRegistry.can_convert('str', 'int')}")
    print(f"  can_convert('any', 'float') -> {DataTypeRegistry.can_convert('any', 'float')}")

    print()


def test_variable_nodes():
    """Test VariableNode features."""
    print("=" * 60)
    print("Testing VariableNode")
    print("=" * 60)

    # Create different types of variables
    float_var = FloatVariable(default_value=3.14)
    print(f"FloatVariable: {float_var.parameter('value').value()}")

    int_var = IntVariable(default_value=42)
    print(f"IntVariable: {int_var.parameter('value').value()}")

    string_var = StringVariable(default_value="Hello World")
    print(f"StringVariable: {string_var.parameter('value').value()}")

    bool_var = BoolVariable(default_value=True)
    print(f"BoolVariable: {bool_var.parameter('value').value()}")

    # Test computation
    float_var.cook()
    result = float_var.get_output_value("out")
    print(f"\nFloatVariable output value: {result}")

    # Change value and re-cook
    float_var.parameter("value").set_value(2.71828)
    print(f"Changed value to: {float_var.parameter('value').value()}")
    print(f"Node is dirty: {float_var.is_dirty()}")  # Should be True after parameter change
    result = float_var.get_output_value("out")  # This triggers cook automatically
    print(f"New output value: {result}")

    print()


def test_variable_with_math():
    """Test VariableNode with math operations."""
    print("=" * 60)
    print("Testing VariableNode with Math Operations")
    print("=" * 60)

    # Create variables
    var_a = FloatVariable(default_value=10.0, name="A")
    var_b = FloatVariable(default_value=5.0, name="B")

    # Create add node
    add = AddNode()

    # Connect variables to add node
    var_a.output("out").connect_to(add.input("a"))
    var_b.output("out").connect_to(add.input("b"))

    # Cook and get result
    result = add.get_output_value("result")
    print(f"A = {var_a.parameter('value').value()}")
    print(f"B = {var_b.parameter('value').value()}")
    print(f"A + B = {result}")

    # Change variable and recalculate
    var_a.parameter("value").set_value(20.0)
    print(f"\nChanged A to: {var_a.parameter('value').value()}")
    print(f"Add node is dirty: {add.is_dirty()}")  # Should be True after upstream change
    result = add.get_output_value("result")  # This triggers cook automatically
    print(f"A + B = {result}")

    print()


def test_multi_connection():
    """Test multi-connection input with MergeNode."""
    print("=" * 60)
    print("Testing Multi-Connection Input (MergeNode)")
    print("=" * 60)

    # Create multiple variables
    var1 = FloatVariable(default_value=1.0, name="Var1")
    var2 = FloatVariable(default_value=2.0, name="Var2")
    var3 = FloatVariable(default_value=3.0, name="Var3")
    var4 = FloatVariable(default_value=4.0, name="Var4")

    # Create merge node
    merge = MergeNode()

    # Connect all variables to merge (multi-connection!)
    var1.output("out").connect_to(merge.input("items"))
    var2.output("out").connect_to(merge.input("items"))
    var3.output("out").connect_to(merge.input("items"))
    var4.output("out").connect_to(merge.input("items"))

    # Check connections
    items_input = merge.input("items")
    print(f"Number of connections: {len(items_input.connections())}")
    print(f"Multi-connection enabled: {items_input.multi_connection}")

    # Cook and get result
    result = merge.get_output_value("list")
    print(f"\nMerged list: {result}")

    # Verify it's a list
    print(f"Type: {type(result)}")
    print(f"Length: {len(result)}")

    print()


def test_multi_connection_with_math():
    """Test multi-connection with mathematical operations."""
    print("=" * 60)
    print("Testing Multi-Connection with Math")
    print("=" * 60)

    # Create variables and compute their sum
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    variables = []

    for i, val in enumerate(values):
        var = FloatVariable(default_value=val, name=f"V{i+1}")
        variables.append(var)

    # Merge all variables
    merge = MergeNode()
    for var in variables:
        var.output("out").connect_to(merge.input("items"))

    # Get merged list
    merged_list = merge.get_output_value("list")
    print(f"Values: {merged_list}")
    print(f"Sum: {sum(merged_list)}")
    print(f"Average: {sum(merged_list) / len(merged_list)}")

    print()


def test_typed_merge():
    """Test TypedMergeNode."""
    print("=" * 60)
    print("Testing TypedMergeNode")
    print("=" * 60)

    # Create float variables
    var1 = FloatVariable(default_value=1.5, name="F1")
    var2 = FloatVariable(default_value=2.5, name="F2")

    # Create typed merge (only accepts floats)
    typed_merge = TypedMergeNode(data_type="float")

    # Connect
    var1.output("out").connect_to(typed_merge.input("items"))
    var2.output("out").connect_to(typed_merge.input("items"))

    # Get result
    result = typed_merge.get_output_value("list")
    print(f"Float merge result: {result}")

    print()


def test_serialization():
    """Test dataclass-based serialization."""
    print("=" * 60)
    print("Testing Serialization (Dataclass)")
    print("=" * 60)

    # Create a variable node
    var = FloatVariable(default_value=3.14, name="Pi")

    # Serialize
    data = var.serialize()
    print("Serialized data:")
    import json
    print(json.dumps(data, indent=2, default=str))

    print()


def test_custom_data_type():
    """Test custom data type registration."""
    print("=" * 60)
    print("Testing Custom Data Type (pathlib.Path)")
    print("=" * 60)

    # Register Path type (already done in test_data_type_registry)
    if not DataTypeRegistry.is_registered("Path"):
        DataTypeRegistry.register("Path", Path)

    # Create a Path variable
    path_var = VariableNode(
        data_type="Path",
        default_value=Path("/tmp/test.txt"),
        name="FilePath"
    )

    # Get value
    result = path_var.get_output_value("out")
    print(f"Path variable value: {result}")
    print(f"Type: {type(result)}")
    print(f"Is Path instance: {isinstance(result, Path)}")

    print()


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("New Features Test Suite")
    print("=" * 60 + "\n")

    test_data_type_registry()
    test_variable_nodes()
    test_variable_with_math()
    test_multi_connection()
    test_multi_connection_with_math()
    test_typed_merge()
    test_serialization()
    test_custom_data_type()

    print("=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
