"""
Tests for Topological Execution Order
=======================================

Test that network execution uses correct topological order
and avoids redundant computation.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodegraph.core.models import NetworkModel
from nodegraph.nodes.operators import AddNode, MultiplyNode
from nodegraph.nodes.base import FloatVariable


def test_execution_order_simple():
    """Test that execution order is correct for simple linear network."""
    network = NetworkModel(name="LinearTest")

    # Create linear chain: A -> Add -> Mul
    var_a = FloatVariable(default_value=2.0, name="A")
    add = AddNode()
    add.name = "Add"
    mul = MultiplyNode()
    mul.name = "Mul"

    # Add in reverse order
    network.add_node(mul)
    network.add_node(add)
    network.add_node(var_a)

    network.connect(var_a.id, "out", add.id, "a")
    network.connect(add.id, "result", mul.id, "a")

    # Get execution order
    order = network.get_execution_order()

    assert len(order) == 3

    # Verify order: var_a before add, add before mul
    indices = {node.id: i for i, node in enumerate(order)}
    assert indices[var_a.id] < indices[add.id]
    assert indices[add.id] < indices[mul.id]

    print("✓ Simple execution order correct")


def test_execution_order_diamond():
    """Test execution order for diamond-shaped network."""
    network = NetworkModel(name="DiamondTest")

    #   Var ──┬──> Add1 ──┐
    #         │           ├──> Mul
    #         └──> Add2 ──┘

    var = FloatVariable(default_value=1.0, name="Var")
    add1 = AddNode()
    add1.name = "Add1"
    add2 = AddNode()
    add2.name = "Add2"
    mul = MultiplyNode()
    mul.name = "Mul"

    # Add in random order
    network.add_node(mul)
    network.add_node(add1)
    network.add_node(var)
    network.add_node(add2)

    network.connect(var.id, "out", add1.id, "a")
    network.connect(var.id, "out", add2.id, "a")
    network.connect(add1.id, "result", mul.id, "a")
    network.connect(add2.id, "result", mul.id, "b")

    # Get execution order
    order = network.get_execution_order()

    assert len(order) == 4

    # Verify: var before add1/add2, add1/add2 before mul
    indices = {node.id: i for i, node in enumerate(order)}
    assert indices[var.id] < indices[add1.id]
    assert indices[var.id] < indices[add2.id]
    assert indices[add1.id] < indices[mul.id]
    assert indices[add2.id] < indices[mul.id]

    print("✓ Diamond execution order correct")


def test_execute_no_redundant_computation():
    """Test that execute doesn't cause redundant computation with caching enabled."""
    network = NetworkModel(name="RedundantTest")

    # Track compute calls
    compute_calls = {}

    class TrackedAddNode(AddNode):
        def compute(self, **inputs):
            if self.name not in compute_calls:
                compute_calls[self.name] = 0
            compute_calls[self.name] += 1
            return super().compute(**inputs)

    #   Var ──┬──> Add1 ──┐
    #         │           ├──> Add3
    #         └──> Add2 ──┘

    var = FloatVariable(default_value=1.0, name="Var")
    add1 = TrackedAddNode()
    add1.name = "Add1"
    add2 = TrackedAddNode()
    add2.name = "Add2"
    add3 = TrackedAddNode()
    add3.name = "Add3"

    # Add in worst possible order
    network.add_node(add3)
    network.add_node(add2)
    network.add_node(add1)
    network.add_node(var)

    network.connect(var.id, "out", add1.id, "a")
    network.connect(var.id, "out", add2.id, "a")
    network.connect(add1.id, "result", add3.id, "a")
    network.connect(add2.id, "result", add3.id, "b")

    # Enable caching to avoid redundant computation
    # (When caching is disabled, nodes are always dirty and will recompute)
    for node in network.nodes():
        node.enable_caching = True

    # Execute the final node (Add3)
    compute_calls.clear()
    add3.execute()

    # Each node should be computed exactly once
    assert compute_calls.get("Add1", 0) == 1, f"Add1 computed {compute_calls.get('Add1', 0)} times"
    assert compute_calls.get("Add2", 0) == 1, f"Add2 computed {compute_calls.get('Add2', 0)} times"
    assert compute_calls.get("Add3", 0) == 1, f"Add3 computed {compute_calls.get('Add3', 0)} times"

    total = sum(compute_calls.values())
    assert total == 3, f"Total computes: {total}, expected 3"

    print("✓ No redundant computation in execute (with caching)")


def test_execute_result_correctness():
    """Test that execute produces correct results."""
    network = NetworkModel(name="CorrectnessTest")

    # (A + B) * C
    var_a = FloatVariable(default_value=2.0, name="A")
    var_b = FloatVariable(default_value=3.0, name="B")
    var_c = FloatVariable(default_value=4.0, name="C")
    add = AddNode()
    add.name = "Add"
    mul = MultiplyNode()
    mul.name = "Mul"

    # Add in reverse order
    network.add_node(mul)
    network.add_node(add)
    network.add_node(var_c)
    network.add_node(var_b)
    network.add_node(var_a)

    network.connect(var_a.id, "out", add.id, "a")
    network.connect(var_b.id, "out", add.id, "b")
    network.connect(add.id, "result", mul.id, "a")
    network.connect(var_c.id, "out", mul.id, "b")

    # Execute the final node
    mul.execute()

    # Verify result: (2 + 3) * 4 = 20
    result = mul.get_output_value("result")
    assert result == 20.0

    print("✓ execute produces correct results")


def test_execution_order_independent_nodes():
    """Test execution order with independent node groups."""
    network = NetworkModel(name="IndependentTest")

    # Two independent chains
    # Chain 1: A -> Add1
    # Chain 2: B -> Add2

    var_a = FloatVariable(default_value=1.0, name="A")
    var_b = FloatVariable(default_value=2.0, name="B")
    add1 = AddNode()
    add1.name = "Add1"
    add2 = AddNode()
    add2.name = "Add2"

    network.add_node(add2)
    network.add_node(add1)
    network.add_node(var_b)
    network.add_node(var_a)

    network.connect(var_a.id, "out", add1.id, "a")
    network.connect(var_b.id, "out", add2.id, "a")

    # Get execution order
    order = network.get_execution_order()

    assert len(order) == 4

    # Verify dependencies within each chain
    indices = {node.id: i for i, node in enumerate(order)}
    assert indices[var_a.id] < indices[add1.id]
    assert indices[var_b.id] < indices[add2.id]

    print("✓ Independent nodes execution order correct")


def test_execution_order_empty_network():
    """Test execution order for empty network."""
    network = NetworkModel(name="EmptyTest")

    order = network.get_execution_order()

    assert len(order) == 0
    assert order == []

    print("✓ Empty network execution order correct")


def test_execute_with_caching():
    """Test execute with caching enabled."""
    network = NetworkModel(name="CachingTest")

    var = FloatVariable(default_value=5.0, name="Var")
    add = AddNode()
    add.name = "Add"

    network.add_node(add)
    network.add_node(var)

    network.connect(var.id, "out", add.id, "a")

    # Enable caching
    for node in network.nodes():
        node.enable_caching = True

    # First execute
    add.execute()
    result1 = add.get_output_value("result")

    # All nodes should be clean now
    assert not var.is_dirty()
    assert not add.is_dirty()

    # Second execute (should use cache)
    add.execute()
    result2 = add.get_output_value("result")

    assert result1 == result2

    print("✓ execute with caching works")


def test_cycle_detection_simple():
    """Test that simple cycles are prevented during connect."""
    network = NetworkModel(name="CycleTest")

    add1 = AddNode()
    add1.name = "Add1"
    add2 = AddNode()
    add2.name = "Add2"

    network.add_node(add1)
    network.add_node(add2)

    # Create first connection: Add1 -> Add2
    success1 = network.connect(add1.id, "result", add2.id, "a")
    assert success1, "First connection should succeed"

    # Try to create cycle: Add2 -> Add1 (should fail)
    success2 = network.connect(add2.id, "result", add1.id, "a")
    assert not success2, "Second connection should fail (would create cycle)"

    # Verify cycle was prevented
    assert not add1.input("a").is_connected()

    print("✓ Simple cycle detection works")


def test_cycle_detection_in_connect():
    """Test that connect prevents cyclic connections."""
    network = NetworkModel(name="CycleTest")

    add1 = AddNode()
    add1.name = "Add1"
    add2 = AddNode()
    add2.name = "Add2"

    network.add_node(add1)
    network.add_node(add2)

    # Create first connection
    success1 = network.connect(add1.id, "result", add2.id, "a")
    assert success1, "First connection should succeed"

    # Try to create cycle (should fail)
    success2 = network.connect(add2.id, "result", add1.id, "a")
    assert not success2, "Second connection should fail (would create cycle)"

    # Verify the cycle-creating connection was not made
    assert not add1.input("a").is_connected()

    print("✓ connect cycle detection works")


def test_cycle_detection_partial():
    """Test that connect prevents cycles in partially connected graphs."""
    network = NetworkModel(name="PartialCycleTest")

    var = FloatVariable(default_value=1.0, name="Var")
    add1 = AddNode()
    add1.name = "Add1"
    add2 = AddNode()
    add2.name = "Add2"
    add3 = AddNode()
    add3.name = "Add3"

    network.add_node(var)
    network.add_node(add1)
    network.add_node(add2)
    network.add_node(add3)

    # Var -> Add1 -> Add2
    #     -> Add3
    success1 = network.connect(var.id, "out", add1.id, "a")
    success2 = network.connect(add1.id, "result", add2.id, "a")
    success3 = network.connect(var.id, "out", add3.id, "a")

    assert success1 and success2 and success3, "Initial connections should succeed"

    # Try to create cycle: Add2 -> Add1 (should fail)
    success4 = network.connect(add2.id, "result", add1.id, "b")
    assert not success4, "Cycle-creating connection should be prevented"

    # Verify Add3 is still connected (not affected by cycle prevention)
    assert add3.input("a").is_connected()

    print("✓ Partial cycle detection works")


def test_has_cycle_method():
    """Test the has_cycle() utility method."""
    # Test without cycle
    network1 = NetworkModel(name="NoCycle")
    var = FloatVariable(default_value=1.0, name="Var")
    add = AddNode()
    network1.add_node(var)
    network1.add_node(add)
    network1.connect(var.id, "out", add.id, "a")

    assert not network1.has_cycle()

    # Test with cycle (need to bypass connect() cycle detection)
    network2 = NetworkModel(name="WithCycle")
    add1 = AddNode()
    add2 = AddNode()
    network2.add_node(add1)
    network2.add_node(add2)

    # Create connections directly at connector level to bypass cycle detection
    add1.output("result").connect_to(add2.input("a"))
    add2.output("result").connect_to(add1.input("a"))

    assert network2.has_cycle()

    print("✓ has_cycle() method works")


def run_all_tests():
    """Run all topological execution tests."""
    print("=" * 60)
    print("Topological Execution Tests")
    print("=" * 60)

    test_execution_order_simple()
    test_execution_order_diamond()
    test_execute_no_redundant_computation()
    test_execute_result_correctness()
    test_execution_order_independent_nodes()
    test_execution_order_empty_network()
    test_execute_with_caching()
    test_cycle_detection_simple()
    test_cycle_detection_in_connect()
    test_cycle_detection_partial()
    test_has_cycle_method()

    print("=" * 60)
    print("All topological execution tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
