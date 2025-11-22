"""
Debug test to trace signal flow and find recursion cause.
"""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

from nodegraph.core.models import NetworkModel
from nodegraph.nodes.base.variable_node import IntVariable
from nodegraph.nodes.operators.math_nodes import AddNode
from nodegraph.nodes.utils.output_nodes import PrintNode, DisplayNode
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

    original_on_connector_changed = connection_item.ConnectionItem._on_connector_changed
    original_update = connection_item.ConnectionItem.update
    original_update_path = connection_item.ConnectionItem.update_path

    def debug_on_connector_changed(self):
        trace_call("ConnectionItem._on_connector_changed",
                  f"source={self.source_port.connector.node.name if self.source_port else None} "
                  f"target={self.target_port.connector.node.name if self.target_port else None}")
        call_stack.append("ConnectionItem._on_connector_changed")
        try:
            result = original_on_connector_changed(self)
            return result
        finally:
            call_stack.pop()
            trace_return("ConnectionItem._on_connector_changed")

    def debug_update(self, *args, **kwargs):
        if len(call_stack) > 0:  # Only trace if we're in a call
            trace_call("ConnectionItem.update")
            call_stack.append("ConnectionItem.update")
            try:
                result = original_update(self, *args, **kwargs)
                return result
            finally:
                call_stack.pop()
                trace_return("ConnectionItem.update")
        else:
            return original_update(self, *args, **kwargs)

    def debug_update_path(self):
        if len(call_stack) > 0:  # Only trace if we're in a call
            trace_call("ConnectionItem.update_path")
            call_stack.append("ConnectionItem.update_path")
            try:
                result = original_update_path(self)
                return result
            finally:
                call_stack.pop()
                trace_return("ConnectionItem.update_path")
        else:
            return original_update_path(self)

    connection_item.ConnectionItem._on_connector_changed = debug_on_connector_changed
    connection_item.ConnectionItem.update = debug_update
    connection_item.ConnectionItem.update_path = debug_update_path

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

    def debug_on_parameter_changed(self, param_name, value):
        trace_call("NodeGraphicsItem._on_parameter_changed",
                  f"node={self.node_model.name} param={param_name}")
        call_stack.append(f"NodeGraphicsItem._on_parameter_changed[{self.node_model.name}]")
        try:
            result = original_on_parameter_changed(self, param_name, value)
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

    def debug_resolve_data_type(self, visited=None):
        node_name = self.connector.node.name if self.connector.node else "None"
        port_name = self.connector.name
        direction = "out" if self.is_output else "in"
        trace_call("PortGraphicsItem._resolve_data_type",
                  f"{node_name}.{port_name}[{direction}]")
        call_stack.append(f"PortGraphicsItem._resolve_data_type[{node_name}.{port_name}]")
        try:
            result = original_resolve_data_type(self, visited)
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

def main():
    """Run the debug test."""
    print("Installing debug patches...")
    patch_connector_model()
    patch_connection_item()
    patch_node_graphics_item()
    patch_port_graphics_item()
    patch_network_model()
    print("Debug patches installed.\n")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    try:
        print("="*80)
        print("Creating network and nodes...")
        print("="*80)

        # Create network
        network = NetworkModel()

        # Create nodes
        int_node = IntVariable(name="Int")
        int_node.parameter('value').set_value(42)
        int_node.set_position(0, 0)

        add_node = AddNode(name="Add")
        add_node.set_position(200, 0)

        print_node = PrintNode(name="Print")
        print_node.set_position(400, 100)

        display_node = DisplayNode(name="Display")
        display_node.set_position(400, -100)

        # Add nodes to network
        network.add_node(int_node)
        network.add_node(add_node)
        network.add_node(print_node)
        network.add_node(display_node)

        # Create scene and view
        scene = NetworkScene(network)
        view = NetworkView(scene)
        view.setGeometry(100, 100, 800, 600)
        view.show()

        # Process events to ensure UI is set up
        app.processEvents()

        print("\n" + "="*80)
        print("STEP 1: int->add->print")
        print("="*80)
        network.connect(int_node.id, 'out', add_node.id, 'a')
        app.processEvents()
        network.connect(add_node.id, 'result', print_node.id, 'value')
        app.processEvents()

        print("\n" + "="*80)
        print("STEP 2: add->display")
        print("="*80)
        network.connect(add_node.id, 'result', display_node.id, 'value')
        app.processEvents()

        print("\n" + "="*80)
        print("STEP 3: int->print (THIS SHOULD TRIGGER THE BUG)")
        print("="*80)
        network.connect(int_node.id, 'out', print_node.id, 'value')
        app.processEvents()

        print("\n" + "="*80)
        print("✅ TEST PASSED - No recursion error!")
        print("="*80)

    except RecursionError as e:
        print("\n" + "="*80)
        print(f"❌ RECURSION ERROR CAUGHT: {e}")
        print("="*80)
        print("\nFinal call counts:")
        for func, count in sorted(call_counts.items(), key=lambda x: -x[1]):
            if count > 5:
                print(f"  {func}: {count} calls")
        return 1
    except Exception as e:
        print("\n" + "="*80)
        print(f"❌ ERROR: {e}")
        print("="*80)
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
