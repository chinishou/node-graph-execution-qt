"""
Tests for node path functionality.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False

from nodegraph.core.models import NetworkModel
from nodegraph.nodes.base.variable_node import VariableNode
from nodegraph.nodes.subnet import SubnetNode
from nodegraph.nodes.utils.output_nodes import PrintNode


def test_root_level_node_path():
    """Test path for node at root level."""
    network = NetworkModel("/")

    var_node = VariableNode(data_type="int", name="MyVar")
    network.add_node(var_node)

    assert var_node.get_path() == "/MyVar"


def test_nested_subnet_node_path():
    """Test path for node inside subnet."""
    root = NetworkModel("/")

    # Create subnet
    subnet = SubnetNode(name="MySubnet")
    root.add_node(subnet)

    # Add node inside subnet
    internal_net = subnet.get_internal_network()
    var_node = VariableNode(data_type="int", name="InternalVar")
    internal_net.add_node(var_node)

    assert var_node.get_path() == "/MySubnet/InternalVar"


def test_deeply_nested_subnet_path():
    """Test path for node in deeply nested subnets."""
    root = NetworkModel("/")

    # Level 1 subnet
    subnet1 = SubnetNode(name="Subnet1")
    root.add_node(subnet1)

    # Level 2 subnet
    internal1 = subnet1.get_internal_network()
    subnet2 = SubnetNode(name="Subnet2")
    internal1.add_node(subnet2)

    # Add node in level 2
    internal2 = subnet2.get_internal_network()
    var_node = VariableNode(data_type="int", name="DeepVar")
    internal2.add_node(var_node)

    assert var_node.get_path() == "/Subnet1/Subnet2/DeepVar"


def test_node_path_without_network():
    """Test path for node not in any network."""
    var_node = VariableNode(data_type="int", name="Orphan")

    assert var_node.get_path() == "/Orphan"


def test_print_node_uses_path():
    """Test that PrintNode uses full path in output."""
    from nodegraph.nodes.utils.output_nodes import print_output_signal

    root = NetworkModel("/")
    subnet = SubnetNode(name="TestSubnet")
    root.add_node(subnet)

    internal = subnet.get_internal_network()
    print_node = PrintNode()
    internal.add_node(print_node)

    # Capture signal output
    captured_path = []
    captured_output = []

    def capture(path, output):
        captured_path.append(path)
        captured_output.append(output)

    print_output_signal.connect(capture)

    # Execute print node
    print_node.compute(value="test message")

    assert len(captured_path) == 1
    assert captured_path[0] == "/TestSubnet/Print"
    assert captured_output[0] == "test message"

    print_output_signal.disconnect(capture)


def run_tests():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("Testing Node Path Functionality")
    print("=" * 70)

    tests = [
        ("Root level node path", test_root_level_node_path),
        ("Nested subnet node path", test_nested_subnet_node_path),
        ("Deeply nested subnet path", test_deeply_nested_subnet_path),
        ("Node path without network", test_node_path_without_network),
        ("Print node uses path", test_print_node_uses_path),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            print(f"✓ {name}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {name}: ERROR - {e}")
            failed += 1

    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
