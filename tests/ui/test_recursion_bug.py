"""
Test for recursion bug when connecting across nodes.

Reproducing the issue:
1. int->add->add_1
2. add->add_2
3. int->add_1  <- This causes recursion error

The pattern: when the middle node (add) outputs to multiple nodes,
and the front node (int) connects directly to the FIRST downstream
node (add_1), it triggers recursion. Connecting to add_2 works fine.

Run with visible UI:
    python run_ui_test_visual.py tests/ui/test_recursion_bug.py -s
"""

import pytest
from PySide6.QtWidgets import QApplication

from nodegraph.views import NetworkView, NetworkScene
from nodegraph.core.models import NetworkModel
from nodegraph.nodes.base import IntVariable
from nodegraph.nodes.operators.math_nodes import AddNode


def test_recursion_bug_simple(qtbot, show_ui, ui_delay):
    """Test the recursion bug with simple scenario."""
    # Create network
    network = NetworkModel()

    # Create nodes
    int_node = IntVariable()
    int_node.parameter('value').set_value(10)

    add = AddNode()
    add_1 = AddNode()
    add_2 = AddNode()

    # Set positions for clear visualization
    # Layout: int_node -> add -> add_1
    #                      └─> add_2
    int_node.set_position(100, 200)   # Left
    add.set_position(350, 200)         # Middle
    add_1.set_position(600, 150)       # Top right
    add_2.set_position(600, 250)       # Bottom right

    # Add to network
    network.add_node(int_node)
    network.add_node(add)
    network.add_node(add_1)
    network.add_node(add_2)

    # Create scene and view
    scene = NetworkScene(network)
    view = NetworkView()
    view.set_scene(scene)
    qtbot.addWidget(view)
    view.show()
    qtbot.waitExposed(view)

    # Helper function for event processing
    def maybe_wait(msg=""):
        if show_ui and msg:
            print(f"  {msg}")
        # Always use minimal wait, just process events
        qtbot.wait(10)
        QApplication.processEvents()

    # STEP 1: int->add->add_1
    print("\nSTEP 1: int->add")
    network.connect(int_node.id, 'out', add.id, 'a')
    maybe_wait("Connected int->add")

    print("STEP 1: add->add_1")
    network.connect(add.id, 'result', add_1.id, 'a')
    maybe_wait("Connected add->add_1")

    # STEP 2: add->add_2 (add now has 2 output connections)
    print("\nSTEP 2: add->add_2")
    network.connect(add.id, 'result', add_2.id, 'a')
    maybe_wait("Connected add->add_2 (add now has 2 outputs)")

    # Verify add has 2 output connections
    add_output = add.output('result')
    assert len(add_output._connections) == 2, "Add should have 2 output connections"
    if show_ui:
        print(f"  Verified: add has {len(add_output._connections)} output connections")

    # STEP 3: int->add_1 (THIS CAUSES RECURSION ERROR)
    print("\nSTEP 3: int->add_1 (potential recursion trigger)")
    if show_ui:
        print("  This should disconnect add->add_1 and create int->add_1")
    try:
        network.connect(int_node.id, 'out', add_1.id, 'a')
        # Extra event processing to ensure all deferred updates complete
        QApplication.processEvents()
        QApplication.processEvents()
        scene.update()  # Force scene refresh
        view.viewport().update()  # Force viewport refresh
        maybe_wait("Connected int->add_1 (old add->add_1 should be removed)")
        print("✓ SUCCESS: No recursion error!")
    except RecursionError as e:
        pytest.fail(f"RecursionError occurred: {e}")

    # Verify connections after step 3
    print("\nVerifying final state:")

    # add_1 should only be connected to int, not add
    add_1_input = add_1.input('a')
    assert add_1_input.is_connected()
    assert len(add_1_input._connections) == 1
    assert add_1_input._connections[0] == int_node.output('out')
    print("✓ add_1 connected to int only")

    # add should only be connected to add_2
    add_output = add.output('result')
    connections = list(add_output._connections)
    assert len(connections) == 1
    assert add_2.input('a') in connections
    assert add_1.input('a') not in connections
    print("✓ add connected to add_2 only")

    # Test completed
    if show_ui:
        print("\nTest completed!")


def test_recursion_bug_variant(qtbot, show_ui, ui_delay):
    """Test connecting to add_2 instead (should work fine)."""
    # Create network
    network = NetworkModel()

    # Create nodes
    int_node = IntVariable()
    int_node.parameter('value').set_value(10)

    add = AddNode()
    add_1 = AddNode()
    add_2 = AddNode()

    # Set positions for clear visualization
    # Layout: int_node -> add -> add_1
    #                      └─> add_2
    int_node.set_position(100, 200)   # Left
    add.set_position(350, 200)         # Middle
    add_1.set_position(600, 150)       # Top right
    add_2.set_position(600, 250)       # Bottom right

    # Add to network
    network.add_node(int_node)
    network.add_node(add)
    network.add_node(add_1)
    network.add_node(add_2)

    # Create scene and view
    scene = NetworkScene(network)
    view = NetworkView()
    view.set_scene(scene)
    qtbot.addWidget(view)
    view.show()
    qtbot.waitExposed(view)

    # Helper function for event processing
    def maybe_wait(msg=""):
        if show_ui and msg:
            print(f"  {msg}")
        # Always use minimal wait, just process events
        qtbot.wait(10)
        QApplication.processEvents()

    # STEP 1: int->add->add_1
    print("\nSTEP 1: int->add->add_1")
    network.connect(int_node.id, 'out', add.id, 'a')
    maybe_wait("Connected int->add")

    network.connect(add.id, 'result', add_1.id, 'a')
    maybe_wait("Connected add->add_1")

    # STEP 2: add->add_2
    print("\nSTEP 2: add->add_2")
    network.connect(add.id, 'result', add_2.id, 'a')
    maybe_wait("Connected add->add_2")

    # STEP 3: int->add_2 (this should work fine)
    print("\nSTEP 3: int->add_2 (should work fine, unlike add_1)")
    if show_ui:
        print("  This should disconnect add->add_2 and create int->add_2")
    try:
        network.connect(int_node.id, 'out', add_2.id, 'a')
        # Extra event processing to ensure all deferred updates complete
        QApplication.processEvents()
        QApplication.processEvents()
        scene.update()  # Force scene refresh
        view.viewport().update()  # Force viewport refresh
        maybe_wait("Connected int->add_2")
        print("✓ SUCCESS: No recursion error!")
    except RecursionError as e:
        pytest.fail(f"RecursionError occurred: {e}")

    # Verify connections
    print("\nVerifying final state:")
    add_2_input = add_2.input('a')
    assert add_2_input._connections[0] == int_node.output('out')
    print("✓ add_2 connected to int")

    # Test completed
    if show_ui:
        print("\nTest completed!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
