"""
Tests for Output Nodes
=======================

Test output node functionality:
- PrintNode
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodegraph.nodes.utils.output_nodes import PrintNode, print_output_signal
from nodegraph.nodes.base import FloatVariable


def test_print_node_creation():
    """Test creating a PrintNode."""
    node = PrintNode()

    assert node is not None
    assert node.node_type == "PrintNode"
    assert node.category == "Utils"
    assert "value" in node.inputs()
    assert "prefix" in node.parameters()

    print("✓ PrintNode creation works")


def test_print_node_simple():
    """Test PrintNode with simple value."""
    node = PrintNode()

    # Capture signal output
    signal_output = []

    def capture_output(node_name, output_text):
        signal_output.append((node_name, output_text))

    print_output_signal.connect(capture_output)

    # Set value and cook
    node.input("value").default_value = 42.0
    node.cook()

    # Check signal was emitted
    assert len(signal_output) == 1
    # PrintNode emits full path (e.g., "/Print" for root-level nodes)
    assert signal_output[0][0] == "/Print"
    assert "42" in signal_output[0][1]

    # Cleanup
    print_output_signal.disconnect(capture_output)

    print("✓ PrintNode simple value works")


def test_print_node_with_prefix():
    """Test PrintNode with prefix parameter."""
    node = PrintNode()
    node.name = "TestPrint"

    # Capture signal output
    signal_output = []

    def capture_output(node_name, output_text):
        signal_output.append((node_name, output_text))

    print_output_signal.connect(capture_output)

    # Set prefix and value
    node.parameter("prefix").set_value("Result")
    node.input("value").default_value = 100

    node.cook()

    # Check output includes prefix
    assert len(signal_output) == 1
    # PrintNode emits full path (e.g., "/TestPrint" for root-level nodes)
    assert signal_output[0][0] == "/TestPrint"
    assert "Result:" in signal_output[0][1]
    assert "100" in signal_output[0][1]

    # Cleanup
    print_output_signal.disconnect(capture_output)

    print("✓ PrintNode with prefix works")


def test_print_node_with_connection():
    """Test PrintNode with connected input."""
    var = FloatVariable(default_value=3.14)
    print_node = PrintNode()

    # Capture signal output
    signal_output = []

    def capture_output(node_name, output_text):
        signal_output.append((node_name, output_text))

    print_output_signal.connect(capture_output)

    # Connect
    var.output("out").connect_to(print_node.input("value"))

    # Cook
    var.cook()
    print_node.cook()

    # Check output
    assert len(signal_output) == 1
    assert "3.14" in signal_output[0][1]

    # Cleanup
    print_output_signal.disconnect(capture_output)

    print("✓ PrintNode with connection works")


def test_print_node_with_none():
    """Test PrintNode handles None value."""
    node = PrintNode()

    # Capture signal output
    signal_output = []

    def capture_output(node_name, output_text):
        signal_output.append((node_name, output_text))

    print_output_signal.connect(capture_output)

    # Set None value
    node.input("value").default_value = None
    node.cook()

    # Should emit something
    assert len(signal_output) == 1
    assert "None" in signal_output[0][1]

    # Cleanup
    print_output_signal.disconnect(capture_output)

    print("✓ PrintNode handles None value")


def run_all_tests():
    """Run all output node tests."""
    print("=" * 60)
    print("Output Node Tests")
    print("=" * 60)

    test_print_node_creation()
    test_print_node_simple()
    test_print_node_with_prefix()
    test_print_node_with_connection()
    test_print_node_with_none()

    print("=" * 60)
    print("All output node tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
