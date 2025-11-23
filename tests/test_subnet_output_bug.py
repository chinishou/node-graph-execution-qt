"""
Test subnet output bug
"""
import pytest
from nodegraph.core.models import NetworkModel
from nodegraph.nodes.subnet import SubnetNode
from nodegraph.nodes.base import IntVariable


def test_subnet_output_propagation():
    """Test that subnet output correctly propagates data out."""
    # Create main network
    network = NetworkModel()

    # Create int node
    int_node = IntVariable(default_value=42)
    network.add_node(int_node)

    # Create subnet with input->output
    subnet = SubnetNode(name="Subnet")
    network.add_node(subnet)

    # Get internal network
    internal = subnet.get_internal_network()

    # Add input and output nodes
    input_node = subnet.add_subnet_input("input", "int")
    output_node = subnet.add_subnet_output("output", "int")

    # Connect inside subnet: input->output
    internal.connect(input_node.id, "input", output_node.id, "output")

    # Connect outside: int->subnet
    network.connect(int_node.id, "out", subnet.id, "input")

    # Execute subnet
    result = subnet.execute()

    # Check subnet's output value
    output_value = subnet.get_output_value("output")
    print(f"Subnet output value: {output_value}")

    assert output_value is not None, "Subnet output should not be None"
    assert output_value == 42, f"Expected 42, got {output_value}"

    # Also test getting value from output connector
    subnet_output_conn = subnet.output("output")
    conn_value = subnet_output_conn.get_value()
    print(f"Output connector value: {conn_value}")

    assert conn_value == 42, f"Expected 42 from connector, got {conn_value}"


if __name__ == "__main__":
    test_subnet_output_propagation()
    print("✓ Test passed!")
