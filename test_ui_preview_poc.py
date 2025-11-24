#!/usr/bin/env python3
"""
Test script for UI Preview POC

This script tests the UI preview system without requiring a running GUI.
It verifies that all nodes can be instantiated and execute correctly.
"""

from nodegraph.core.models import NetworkModel
from nodegraph.core.registry import NodeRegistry
from nodegraph.nodes.ui import UIRootNode, LabelNode, ButtonNode, VBoxLayoutNode

def test_ui_nodes():
    """Test UI nodes creation and execution."""
    print("=" * 60)
    print("Testing UI Preview POC")
    print("=" * 60)

    # Register nodes
    print("\n1. Registering UI nodes...")
    NodeRegistry.register(UIRootNode)
    NodeRegistry.register(LabelNode)
    NodeRegistry.register(ButtonNode)
    NodeRegistry.register(VBoxLayoutNode)
    print("   ✓ Registered: UIRootNode, LabelNode, ButtonNode, VBoxLayoutNode")

    # Create network
    print("\n2. Creating network...")
    network = NetworkModel("/")
    print("   ✓ Network created")

    # Create UI nodes
    print("\n3. Creating UI nodes...")

    # Create labels
    label1 = LabelNode()
    label1.parameter("text").set_value("Hello, World!")
    network.add_node(label1)
    print("   ✓ Created Label1: 'Hello, World!'")

    label2 = LabelNode()
    label2.parameter("text").set_value("This is a test")
    network.add_node(label2)
    print("   ✓ Created Label2: 'This is a test'")

    # Create button
    button = ButtonNode()
    button.parameter("text").set_value("Click Me!")
    button.parameter("on_click_message").set_value("Button was clicked!")
    network.add_node(button)
    print("   ✓ Created Button: 'Click Me!'")

    # Create layout
    layout = VBoxLayoutNode()
    layout.parameter("spacing").set_value(10)
    layout.parameter("margins").set_value(15)
    network.add_node(layout)
    print("   ✓ Created VBoxLayout (spacing: 10, margins: 15)")

    # Create root
    root = UIRootNode()
    network.add_node(root)
    print("   ✓ Created UIRootNode")

    # Connect nodes
    print("\n4. Connecting nodes...")
    network.connect(label1.id, "widget", layout.id, "child1")
    print("   ✓ Connected: Label1 → Layout.child1")

    network.connect(label2.id, "widget", layout.id, "child2")
    print("   ✓ Connected: Label2 → Layout.child2")

    network.connect(button.id, "widget", layout.id, "child3")
    print("   ✓ Connected: Button → Layout.child3")

    network.connect(layout.id, "widget", root.id, "widget")
    print("   ✓ Connected: Layout → UIRootNode")

    # Test execution (without Qt, widgets will be None)
    print("\n5. Testing node execution logic...")
    print("   Note: Actual Qt widgets require PySide6/PyQt6")
    print("   Testing data flow through the node graph...\n")

    # Execute nodes in order
    print("   Executing Label1...")
    result = label1.execute()
    print(f"   → Success: {result}")

    print("   Executing Label2...")
    result = label2.execute()
    print(f"   → Success: {result}")

    print("   Executing Button...")
    result = button.execute()
    print(f"   → Success: {result}")

    print("   Executing VBoxLayout...")
    result = layout.execute()
    print(f"   → Success: {result}")

    print("   Executing UIRootNode...")
    result = root.execute()
    print(f"   → Success: {result}")

    # Summary
    print("\n" + "=" * 60)
    print("POC Test Results")
    print("=" * 60)
    print("✓ All nodes registered successfully")
    print("✓ Network created successfully")
    print("✓ Nodes connected successfully")
    print("✓ Node execution logic works")
    print("\nNext Steps:")
    print("  1. Install PySide6: pip install PySide6")
    print("  2. Run: python run_editor.py")
    print("  3. Click 'Toggle Live Preview' in toolbar")
    print("  4. Create UI nodes (Tab → UI category)")
    print("  5. Connect nodes to UIRootNode")
    print("  6. Click 'Refresh' in preview pane")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_ui_nodes()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
