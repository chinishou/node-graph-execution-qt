"""
Debug test to trace signal flow and find recursion cause.

Uses pytest-qt for Qt testing.

Run with: pytest tests/ui/test_debug_signals.py -v
Or standalone: python tests/ui/test_debug_signals.py
"""
import sys
from pathlib import Path

# Add project root to path for standalone execution
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

from nodegraph.core.models import NetworkModel
from nodegraph.nodes.base.variable_node import IntVariable
from nodegraph.nodes.operators.math_nodes import AddNode
from nodegraph.nodes.utils.output_nodes import PrintNode
from nodegraph.views.network import NetworkScene, NetworkView

# Global counter to track recursion depth
call_stack = []
call_counts = {}

def trace_call(func_name, extra=""):
    """Add a call to the trace."""
    indent = "  " * len(call_stack)
    msg = f"{indent}→ {func_name}"
    if extra:
        msg += f" {extra}"
    print(msg)

    # Track call count
    call_counts[func_name] = call_counts.get(func_name, 0) + 1
    if call_counts[func_name] > 50:
        print(f"\n{'='*80}")
        print(f"⚠️  RECURSION DETECTED: {func_name} called {call_counts[func_name]} times!")
        print(f"{'='*80}")
        print("\nCall stack:")
        for i, name in enumerate(call_stack):
            print(f"  {i}: {name}")
        raise RecursionError(f"Too many calls to {func_name}")

def trace_return(func_name):
    """Remove a call from the trace."""
    indent = "  " * (len(call_stack) - 1)
    print(f"{indent}← {func_name}")

def patch_connection_item():
    """Add debug logging to ConnectionItem."""
    from nodegraph.views.connectors import connection_item

    original_update_path = connection_item.ConnectionItem.update_path
    original_get_connection_color = connection_item.ConnectionItem._get_connection_color

    def debug_update_path(self):
        if len(call_stack) > 0:  # Only trace if we're in a call
            source_name = self.source_port.connector.node.name if self.source_port and self.source_port.connector else "None"
            target_name = self.target_port.connector.node.name if self.target_port and self.target_port.connector else "None"
            trace_call("ConnectionItem.update_path", f"{source_name} -> {target_name}")
            call_stack.append("ConnectionItem.update_path")
            try:
                result = original_update_path(self)
                return result
            finally:
                call_stack.pop()
                trace_return("ConnectionItem.update_path")
        else:
            return original_update_path(self)

    def debug_get_connection_color(self):
        if len(call_stack) > 0:  # Only trace if we're in a call
            trace_call("ConnectionItem._get_connection_color")
            call_stack.append("ConnectionItem._get_connection_color")
            try:
                result = original_get_connection_color(self)
                return result
            finally:
                call_stack.pop()
                trace_return("ConnectionItem._get_connection_color")
        else:
            return original_get_connection_color(self)

    connection_item.ConnectionItem.update_path = debug_update_path
    connection_item.ConnectionItem._get_connection_color = debug_get_connection_color

def patch_node_graphics_item():
    """Add debug logging to NodeGraphicsItem."""
    from nodegraph.views.nodes import node_graphics_item

    original_on_connection_changed = node_graphics_item.NodeGraphicsItem._on_connection_changed
    original_on_parameter_changed = node_graphics_item.NodeGraphicsItem._on_parameter_changed

    def debug_on_connection_changed(self):
        trace_call("NodeGraphicsItem._on_connection_changed", f"node={self.node_model.name}")
        call_stack.append(f"NodeGraphicsItem._on_connection_changed[{self.node_model.name}]")
        try:
            result = original_on_connection_changed(self)
            return result
        finally:
            call_stack.pop()
            trace_return(f"NodeGraphicsItem._on_connection_changed[{self.node_model.name}]")

    def debug_on_parameter_changed(self):
        trace_call("NodeGraphicsItem._on_parameter_changed",
                  f"node={self.node_model.name}")
        call_stack.append(f"NodeGraphicsItem._on_parameter_changed[{self.node_model.name}]")
        try:
            result = original_on_parameter_changed(self)
            return result
        finally:
            call_stack.pop()
            trace_return(f"NodeGraphicsItem._on_parameter_changed[{self.node_model.name}]")

    node_graphics_item.NodeGraphicsItem._on_connection_changed = debug_on_connection_changed
    node_graphics_item.NodeGraphicsItem._on_parameter_changed = debug_on_parameter_changed

def patch_port_graphics_item():
    """Add debug logging to PortGraphicsItem."""
    from nodegraph.views.nodes import port_graphics_item

    original_resolve_data_type = port_graphics_item.PortGraphicsItem._resolve_data_type

    def debug_resolve_data_type(self, visited=None, depth=0):
        node_name = self.connector.node.name if self.connector.node else "None"
        port_name = self.connector.name
        direction = "out" if self.is_output else "in"
        trace_call("PortGraphicsItem._resolve_data_type",
                  f"{node_name}.{port_name}[{direction}]")
        call_stack.append(f"PortGraphicsItem._resolve_data_type[{node_name}.{port_name}]")
        try:
            result = original_resolve_data_type(self, visited, depth)
            return result
        finally:
            call_stack.pop()
            trace_return(f"PortGraphicsItem._resolve_data_type[{node_name}.{port_name}]")

    port_graphics_item.PortGraphicsItem._resolve_data_type = debug_resolve_data_type

def patch_connector_model():
    """Add debug logging to ConnectorModel."""
    from nodegraph.core.models import connector_model

    original_disconnect_from = connector_model.ConnectorModel.disconnect_from
    original_connect_to = connector_model.ConnectorModel.connect_to

    def debug_disconnect_from(self, other):
        self_node = self.node.name if self.node else "None"
        other_node = other.node.name if other.node else "None"
        trace_call("ConnectorModel.disconnect_from",
                  f"{self_node}.{self.name} -> {other_node}.{other.name}")
        call_stack.append(f"ConnectorModel.disconnect_from[{self_node}.{self.name}]")
        try:
            result = original_disconnect_from(self, other)
            return result
        finally:
            call_stack.pop()
            trace_return(f"ConnectorModel.disconnect_from[{self_node}.{self.name}]")

    def debug_connect_to(self, other):
        self_node = self.node.name if self.node else "None"
        other_node = other.node.name if other.node else "None"
        trace_call("ConnectorModel.connect_to",
                  f"{self_node}.{self.name} -> {other_node}.{other.name}")
        call_stack.append(f"ConnectorModel.connect_to[{self_node}.{self.name}]")
        try:
            result = original_connect_to(self, other)
            return result
        finally:
            call_stack.pop()
            trace_return(f"ConnectorModel.connect_to[{self_node}.{self.name}]")

    connector_model.ConnectorModel.disconnect_from = debug_disconnect_from
    connector_model.ConnectorModel.connect_to = debug_connect_to

def patch_network_model():
    """Add debug logging to NetworkModel."""
    from nodegraph.core.models import network_model

    original_connect = network_model.NetworkModel.connect
    original_disconnect = network_model.NetworkModel.disconnect

    def debug_connect(self, source_node_id, source_output, target_node_id, target_input):
        source_node = self.get_node(source_node_id)
        target_node = self.get_node(target_node_id)
        print(f"\n{'='*80}")
        print(f"🔗 NetworkModel.connect: {source_node.name}.{source_output} -> {target_node.name}.{target_input}")
        print(f"{'='*80}")
        call_stack.append(f"NetworkModel.connect")
        try:
            result = original_connect(self, source_node_id, source_output, target_node_id, target_input)
            return result
        finally:
            call_stack.pop()
            print(f"{'='*80}")
            print(f"✓ NetworkModel.connect completed")
            print(f"{'='*80}\n")

    def debug_disconnect(self, source_node_id, source_output, target_node_id, target_input):
        source_node = self.get_node(source_node_id)
        target_node = self.get_node(target_node_id)
        print(f"\n{'='*80}")
        print(f"🔌 NetworkModel.disconnect: {source_node.name}.{source_output} -> {target_node.name}.{target_input}")
        print(f"{'='*80}")
        call_stack.append(f"NetworkModel.disconnect")
        try:
            result = original_disconnect(self, source_node_id, source_output, target_node_id, target_input)
            return result
        finally:
            call_stack.pop()
            print(f"{'='*80}")
            print(f"✓ NetworkModel.disconnect completed")
            print(f"{'='*80}\n")

    network_model.NetworkModel.connect = debug_connect
    network_model.NetworkModel.disconnect = debug_disconnect

def test_signal_flow_with_debug_tracing(qtbot):
    """
    Test signal flow and detect potential recursion issues.

    This test creates a network with connections and traces the signal flow
    to ensure there are no infinite recursion issues.
    """
    # Install debug patches
    patch_connector_model()
    patch_connection_item()
    patch_node_graphics_item()
    patch_port_graphics_item()
    patch_network_model()

    # Clear global counters
    call_stack.clear()
    call_counts.clear()

    # Create network
    network = NetworkModel()

    # Create nodes (don't pass name - they have defaults)
    int_node = IntVariable()
    int_node.parameter('value').set_value(42)
    int_node.set_position(0, 0)

    add_node = AddNode()
    add_node.set_position(200, 0)

    print_node = PrintNode()
    print_node.set_position(400, 100)

    print_node_2 = PrintNode()
    print_node_2.set_position(400, -100)

    # Add nodes to network
    network.add_node(int_node)
    network.add_node(add_node)
    network.add_node(print_node)
    network.add_node(print_node_2)

    # Create scene and view
    scene = NetworkScene(network)
    view = NetworkView()
    view.set_scene(scene)
    qtbot.addWidget(view)
    view.show()
    qtbot.waitExposed(view)

    # STEP 1: int->add->print
    print("\n" + "="*80)
    print("STEP 1: Building initial network (Int->Add, Add->Print)")
    print("="*80)
    call_counts.clear()  # Reset counter for this step

    network.connect(int_node.id, 'out', add_node.id, 'a')
    qtbot.wait(10)
    network.connect(add_node.id, 'result', print_node.id, 'value')
    qtbot.wait(10)

    step1_calls = sum(call_counts.values())
    print(f"\nSTEP 1 Total calls: {step1_calls}")
    for func, count in sorted(call_counts.items()):
        if count > 0:
            print(f"  {func}: {count}")

    # STEP 2: add->print_2 (add now has 2 outputs)
    print("\n" + "="*80)
    print("STEP 2: Add second output (Add->Print_1)")
    print("="*80)
    call_counts.clear()  # Reset counter for this step

    network.connect(add_node.id, 'result', print_node_2.id, 'value')
    qtbot.wait(10)

    step2_calls = sum(call_counts.values())
    print(f"\nSTEP 2 Total calls: {step2_calls}")
    for func, count in sorted(call_counts.items()):
        if count > 0:
            print(f"  {func}: {count}")

    # STEP 3: int->print (potential recursion trigger)
    # This should automatically disconnect the old add->print connection
    print("\n" + "="*80)
    print("STEP 3: Replace connection (Int->Print, auto-disconnects Add->Print)")
    print("="*80)
    call_counts.clear()  # Reset counter for this step

    network.connect(int_node.id, 'out', print_node.id, 'value')
    qtbot.wait(10)

    step3_calls = sum(call_counts.values())
    print(f"\nSTEP 3 Total calls: {step3_calls}")
    for func, count in sorted(call_counts.items()):
        if count > 0:
            print(f"  {func}: {count}")

    print("\n" + "="*80)
    print(f"TOTAL across all steps: {step1_calls + step2_calls + step3_calls}")
    print("="*80)

    # Verify print node only has connection from int (old add->print should be disconnected)
    print_input = print_node.input('value')
    assert print_input.is_connected(), "Print input should still be connected"
    connections = print_input._connections
    assert len(connections) == 1, f"Print should have exactly 1 connection, has {len(connections)}"
    assert connections[0] == int_node.output('out'), "Print should be connected to int, not add"

    # Verify add->print is disconnected
    add_output = add_node.output('result')
    add_connections = [c for c in add_output._connections]
    assert print_node.input('value') not in add_connections, "Add should not be connected to print anymore"

    # Verify add->print_2 is still connected
    assert print_node_2.input('value') in add_connections, "Add->print_2 connection should remain"

    # Verify no excessive recursion occurred
    for func, count in call_counts.items():
        assert count < 50, f"Potential recursion: {func} called {count} times"

    # Test passes if we reach here without RecursionError
