"""
Tests for Operator Nodes
=========================

Test mathematical operator nodes:
- AddNode
- SubtractNode
- MultiplyNode
- DivideNode
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodegraph.nodes.operators import AddNode, SubtractNode, MultiplyNode, DivideNode
from nodegraph.nodes.base import FloatVariable


def test_add_node():
    """Test AddNode functionality."""
    add = AddNode()

    # Set input values
    add.input("a").default_value = 5.0
    add.input("b").default_value = 3.0

    # Compute
    result = add.get_output_value("result")
    assert result == 8.0

    print("✓ AddNode works")


def test_add_node_with_connections():
    """Test AddNode with variable inputs."""
    var_a = FloatVariable(default_value=10.0)
    var_b = FloatVariable(default_value=7.5)
    add = AddNode()

    # Connect
    var_a.output("out").connect_to(add.input("a"))
    var_b.output("out").connect_to(add.input("b"))

    # Compute
    result = add.get_output_value("result")
    assert result == 17.5

    print("✓ AddNode with connections works")


def test_subtract_node():
    """Test SubtractNode functionality."""
    sub = SubtractNode()

    # Set input values
    sub.input("a").default_value = 10.0
    sub.input("b").default_value = 3.0

    # Compute
    result = sub.get_output_value("result")
    assert result == 7.0

    print("✓ SubtractNode works")


def test_subtract_node_negative():
    """Test SubtractNode with negative result."""
    sub = SubtractNode()

    sub.input("a").default_value = 3.0
    sub.input("b").default_value = 10.0

    result = sub.get_output_value("result")
    assert result == -7.0

    print("✓ SubtractNode negative result works")


def test_subtract_node_with_connections():
    """Test SubtractNode with variable inputs."""
    var_a = FloatVariable(default_value=20.0)
    var_b = FloatVariable(default_value=8.0)
    sub = SubtractNode()

    # Connect
    var_a.output("out").connect_to(sub.input("a"))
    var_b.output("out").connect_to(sub.input("b"))

    # Compute
    result = sub.get_output_value("result")
    assert result == 12.0

    print("✓ SubtractNode with connections works")


def test_multiply_node():
    """Test MultiplyNode functionality."""
    mul = MultiplyNode()

    # Set input values
    mul.input("a").default_value = 4.0
    mul.input("b").default_value = 5.0

    # Compute
    result = mul.get_output_value("result")
    assert result == 20.0

    print("✓ MultiplyNode works")


def test_multiply_node_with_zero():
    """Test MultiplyNode with zero."""
    mul = MultiplyNode()

    mul.input("a").default_value = 100.0
    mul.input("b").default_value = 0.0

    result = mul.get_output_value("result")
    assert result == 0.0

    print("✓ MultiplyNode with zero works")


def test_multiply_node_with_connections():
    """Test MultiplyNode with variable inputs."""
    var_a = FloatVariable(default_value=3.5)
    var_b = FloatVariable(default_value=2.0)
    mul = MultiplyNode()

    # Connect
    var_a.output("out").connect_to(mul.input("a"))
    var_b.output("out").connect_to(mul.input("b"))

    # Compute
    result = mul.get_output_value("result")
    assert result == 7.0

    print("✓ MultiplyNode with connections works")


def test_divide_node():
    """Test DivideNode functionality."""
    div = DivideNode()

    # Set input values
    div.input("a").default_value = 20.0
    div.input("b").default_value = 4.0

    # Compute
    result = div.get_output_value("result")
    assert result == 5.0

    print("✓ DivideNode works")


def test_divide_node_decimal():
    """Test DivideNode with decimal result."""
    div = DivideNode()

    div.input("a").default_value = 7.0
    div.input("b").default_value = 2.0

    result = div.get_output_value("result")
    assert result == 3.5

    print("✓ DivideNode decimal result works")


def test_divide_by_zero():
    """Test DivideNode division by zero handling."""
    div = DivideNode()

    div.input("a").default_value = 10.0
    div.input("b").default_value = 0.0

    # Division by zero should raise error or return special value
    try:
        result = div.get_output_value("result")
        # If it returns a value, it should be inf or handle gracefully
        assert result is not None
        print("✓ DivideNode handles division by zero")
    except ZeroDivisionError:
        print("✓ DivideNode raises ZeroDivisionError for division by zero")


def test_divide_node_with_connections():
    """Test DivideNode with variable inputs."""
    var_a = FloatVariable(default_value=100.0)
    var_b = FloatVariable(default_value=5.0)
    div = DivideNode()

    # Connect
    var_a.output("out").connect_to(div.input("a"))
    var_b.output("out").connect_to(div.input("b"))

    # Compute
    result = div.get_output_value("result")
    assert result == 20.0

    print("✓ DivideNode with connections works")


def test_chained_operations():
    """Test chaining multiple operations: (10 + 5) * 2 - 6 / 3"""
    # Variables
    var_10 = FloatVariable(default_value=10.0, name="10")
    var_5 = FloatVariable(default_value=5.0, name="5")
    var_2 = FloatVariable(default_value=2.0, name="2")
    var_6 = FloatVariable(default_value=6.0, name="6")
    var_3 = FloatVariable(default_value=3.0, name="3")

    # Operations
    add = AddNode()      # 10 + 5 = 15
    mul = MultiplyNode() # 15 * 2 = 30
    div = DivideNode()   # 6 / 3 = 2
    sub = SubtractNode() # 30 - 2 = 28

    # Connect: (10 + 5)
    var_10.output("out").connect_to(add.input("a"))
    var_5.output("out").connect_to(add.input("b"))

    # Connect: result * 2
    add.output("result").connect_to(mul.input("a"))
    var_2.output("out").connect_to(mul.input("b"))

    # Connect: 6 / 3
    var_6.output("out").connect_to(div.input("a"))
    var_3.output("out").connect_to(div.input("b"))

    # Connect: mul_result - div_result
    mul.output("result").connect_to(sub.input("a"))
    div.output("result").connect_to(sub.input("b"))

    # Compute final result
    result = sub.get_output_value("result")
    assert result == 28.0

    print("✓ Chained operations work")


def test_node_setup():
    """Test that nodes setup their inputs/outputs correctly."""
    # Test AddNode setup
    add = AddNode()
    assert "a" in add.inputs()
    assert "b" in add.inputs()
    assert "result" in add.outputs()
    assert add.category == "Math"

    # Test SubtractNode setup
    sub = SubtractNode()
    assert "a" in sub.inputs()
    assert "b" in sub.inputs()
    assert "result" in sub.outputs()
    assert sub.category == "Math"

    # Test MultiplyNode setup
    mul = MultiplyNode()
    assert "a" in mul.inputs()
    assert "b" in mul.inputs()
    assert "result" in mul.outputs()
    assert mul.category == "Math"

    # Test DivideNode setup
    div = DivideNode()
    assert "a" in div.inputs()
    assert "b" in div.inputs()
    assert "result" in div.outputs()
    assert div.category == "Math"

    print("✓ Node setup works for all operator nodes")


def run_all_tests():
    """Run all operator tests."""
    print("=" * 60)
    print("Operator Node Tests")
    print("=" * 60)

    test_add_node()
    test_add_node_with_connections()
    test_subtract_node()
    test_subtract_node_negative()
    test_subtract_node_with_connections()
    test_multiply_node()
    test_multiply_node_with_zero()
    test_multiply_node_with_connections()
    test_divide_node()
    test_divide_node_decimal()
    test_divide_by_zero()
    test_divide_node_with_connections()
    test_chained_operations()
    test_node_setup()

    print("=" * 60)
    print("All operator tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
