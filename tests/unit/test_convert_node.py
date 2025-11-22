"""
Tests for ConvertNode
======================

Test type conversion node functionality:
- ConvertNode (int, float, bool, str conversions)
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodegraph.nodes.operators.convert_node import ConvertNode
from nodegraph.nodes.base import FloatVariable


def test_convert_node_creation():
    """Test creating a ConvertNode."""
    node = ConvertNode()

    assert node is not None
    assert node.node_type == "ConvertNode"
    assert node.category == "Operators"
    assert "value" in node.inputs()
    assert "result" in node.outputs()
    assert "output_type" in node.parameters()

    print("✓ ConvertNode creation works")


def test_convert_to_int():
    """Test converting values to int."""
    node = ConvertNode()

    # Set output type to int
    node.parameter("output_type").set_value("int")

    # Test float to int
    node.input("value").default_value = 3.7
    node.cook()
    result = node.get_output_value("result")
    assert result == 3
    assert isinstance(result, int)

    # Test string to int
    node.input("value").default_value = "42"
    node.cook()
    result = node.get_output_value("result")
    assert result == 42
    assert isinstance(result, int)

    print("✓ Convert to int works")


def test_convert_to_float():
    """Test converting values to float."""
    node = ConvertNode()

    # Set output type to float
    node.parameter("output_type").set_value("float")

    # Test int to float
    node.input("value").default_value = 42
    node.cook()
    result = node.get_output_value("result")
    assert result == 42.0
    assert isinstance(result, float)

    # Test string to float
    node.input("value").default_value = "3.14"
    node.cook()
    result = node.get_output_value("result")
    assert result == 3.14
    assert isinstance(result, float)

    print("✓ Convert to float works")


def test_convert_to_bool():
    """Test converting values to bool."""
    node = ConvertNode()

    # Set output type to bool
    node.parameter("output_type").set_value("bool")

    # Test int to bool
    node.input("value").default_value = 1
    node.cook()
    result = node.get_output_value("result")
    assert result is True

    node.input("value").default_value = 0
    node.cook()
    result = node.get_output_value("result")
    assert result is False

    # Test string to bool
    node.input("value").default_value = "text"
    node.cook()
    result = node.get_output_value("result")
    assert result is True

    node.input("value").default_value = ""
    node.cook()
    result = node.get_output_value("result")
    assert result is False

    print("✓ Convert to bool works")


def test_convert_to_str():
    """Test converting values to string."""
    node = ConvertNode()

    # Set output type to str
    node.parameter("output_type").set_value("str")

    # Test int to str
    node.input("value").default_value = 42
    node.cook()
    result = node.get_output_value("result")
    assert result == "42"
    assert isinstance(result, str)

    # Test float to str
    node.input("value").default_value = 3.14
    node.cook()
    result = node.get_output_value("result")
    assert result == "3.14"
    assert isinstance(result, str)

    # Test bool to str
    node.input("value").default_value = True
    node.cook()
    result = node.get_output_value("result")
    assert result == "True"
    assert isinstance(result, str)

    print("✓ Convert to str works")


def test_convert_with_connection():
    """Test ConvertNode with connected input."""
    var = FloatVariable(default_value=3.7)
    convert = ConvertNode()

    # Set output type to int
    convert.parameter("output_type").set_value("int")

    # Connect
    var.output("out").connect_to(convert.input("value"))

    # Cook
    var.cook()
    convert.cook()

    result = convert.get_output_value("result")
    assert result == 3
    assert isinstance(result, int)

    print("✓ ConvertNode with connection works")


def test_convert_invalid_conversion():
    """Test conversion with invalid input (should handle gracefully)."""
    node = ConvertNode()

    # Try to convert non-numeric string to int
    node.parameter("output_type").set_value("int")
    node.input("value").default_value = "not a number"

    node.cook()
    result = node.get_output_value("result")

    # Should return original value on conversion failure
    assert result == "not a number"

    print("✓ Invalid conversion handled gracefully")


def test_transforms_data_type():
    """Test that ConvertNode reports it transforms data types."""
    node = ConvertNode()

    assert node.transforms_data_type() is True

    print("✓ transforms_data_type works")


def run_all_tests():
    """Run all convert node tests."""
    print("=" * 60)
    print("ConvertNode Tests")
    print("=" * 60)

    test_convert_node_creation()
    test_convert_to_int()
    test_convert_to_float()
    test_convert_to_bool()
    test_convert_to_str()
    test_convert_with_connection()
    test_convert_invalid_conversion()
    test_transforms_data_type()

    print("=" * 60)
    print("All ConvertNode tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
