"""
Port Graphics Item
==================

QGraphicsItem for rendering port (connector) in the network view.
"""

from PySide6.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...core.models import ConnectorModel


class PortGraphicsItem(QGraphicsItem):
    """
    Graphics item for rendering a port (connector).

    Small circle that can be clicked to create connections.
    """

    PORT_RADIUS = 6

    # Colors by data type
    TYPE_COLORS = {
        'int': QColor(100, 200, 255),      # Light blue
        'float': QColor(150, 255, 150),    # Light green
        'bool': QColor(255, 100, 100),     # Light red
        'str': QColor(255, 200, 100),      # Orange
        'any': QColor(200, 200, 200),      # Gray
    }
    CUSTOM_TYPE_COLOR = QColor(200, 150, 255)  # Purple for custom types
    HOVER_COLOR = QColor(255, 255, 255)

    def __init__(self, connector: "ConnectorModel", is_output: bool, parent=None):
        super().__init__(parent)

        self.connector = connector
        self.is_output = is_output
        self._is_hovered = False

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)

    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle."""
        r = self.PORT_RADIUS + 2
        return QRectF(-r, -r, 2 * r, 2 * r)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        """Paint the port."""
        painter.setRenderHint(QPainter.Antialiasing)

        # Determine color based on hover state or data type
        if self._is_hovered:
            color = self.HOVER_COLOR
        else:
            # Get the actual data type to use for coloring
            data_type = self._resolve_data_type()

            # Get color based on data type
            if data_type in self.TYPE_COLORS:
                color = self.TYPE_COLORS[data_type]
            else:
                # Custom type - use purple
                color = self.CUSTOM_TYPE_COLOR

            # If connected, make color brighter
            if self.connector.is_connected():
                color = color.lighter(130)

        # Draw port circle
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        painter.drawEllipse(QPointF(0, 0), self.PORT_RADIUS, self.PORT_RADIUS)

    def _resolve_data_type(self, visited=None) -> str:
        """
        Recursively resolve the actual data type for this port.

        For 'any' type ports, this will traverse the connection graph to find
        a concrete type, check node parameters, or fall back to 'any'.
        This makes the color resolution work for all nodes universally.

        Strategy priority differs for input vs output ports:
        - Input ports: Connected type > Node parameters > Pass-through
        - Output ports: Node parameters > Connected type > Pass-through

        Args:
            visited: Set of already visited connectors to prevent infinite loops

        Returns:
            The resolved data type string
        """
        if visited is None:
            visited = set()

        # Prevent infinite loops
        connector_id = id(self.connector)
        if connector_id in visited:
            return 'any'
        visited.add(connector_id)

        data_type = self.connector.data_type

        # If not 'any', return the concrete type immediately
        if data_type != 'any':
            return data_type

        # Special handling for SubnetNode and SubnetInputNode/SubnetOutputNode
        if self.connector.node:
            node = self.connector.node
            node_type = getattr(node, 'node_type', None)

            # SubnetNode external output: Check internal SubnetOutputNode
            if node_type == 'SubnetNode' and self.is_output:
                try:
                    from ...nodes.subnet.subnet_node import SubnetNode
                    from ...nodes.subnet.subnet_io_nodes import SubnetOutputNode

                    if isinstance(node, SubnetNode):
                        internal_network = node.get_internal_network()
                        # Find the SubnetOutputNode with matching connector name
                        for internal_node in internal_network.nodes():
                            if isinstance(internal_node, SubnetOutputNode):
                                if internal_node.get_connector_name() == self.connector.name:
                                    # Get the input connector on the SubnetOutputNode
                                    internal_input = internal_node.input(self.connector.name)
                                    if internal_input and internal_input.is_connected():
                                        # Recursively resolve the type of what's connected to it
                                        connections = internal_input.connections()
                                        if connections:
                                            connected_connector = connections[0]
                                            scene = self.scene()
                                            if scene and hasattr(scene, '_node_items'):
                                                if hasattr(connected_connector, 'node') and connected_connector.node:
                                                    node_item = scene._node_items.get(connected_connector.node.id)
                                                    if node_item:
                                                        port = node_item.get_port(connected_connector.name, is_output=True)
                                                        if port:
                                                            resolved = port._resolve_data_type(visited)
                                                            if resolved != 'any':
                                                                return resolved
                except ImportError:
                    pass

            # SubnetInputNode internal output: Check external connection to parent SubnetNode
            if node_type == 'SubnetInputNode' and self.is_output:
                try:
                    from ...nodes.subnet.subnet_io_nodes import SubnetInputNode

                    if isinstance(node, SubnetInputNode):
                        # Check if the node has a reference to parent subnet
                        if hasattr(node, '_parent_subnet') and node._parent_subnet:
                            parent_subnet = node._parent_subnet
                            connector_name = node.get_connector_name()
                            external_input = parent_subnet.input(connector_name)
                            if external_input and external_input.is_connected():
                                # Get what's connected to the external input
                                connections = external_input.connections()
                                if connections:
                                    connected_connector = connections[0]
                                    if hasattr(connected_connector, 'node') and connected_connector.node:
                                        scene = self.scene()
                                        if scene and hasattr(scene, '_node_items'):
                                            node_item = scene._node_items.get(connected_connector.node.id)
                                            if node_item:
                                                port = node_item.get_port(connected_connector.name, is_output=True)
                                                if port:
                                                    resolved = port._resolve_data_type(visited)
                                                    if resolved != 'any':
                                                        return resolved
                except ImportError:
                    pass

        # For 'any' type ports, use different strategies based on port direction

        if self.is_output:
            # OUTPUT PORT: Parameters take priority (e.g., Math node type determines output)

            # Strategy 1: Check node parameters first for outputs
            if self.connector.node:
                for param_name in ['type', 'output_type', 'data_type', 'value_type']:
                    param = self.connector.node.parameter(param_name)
                    if param:
                        param_value = param.value()
                        if param_value in self.TYPE_COLORS:
                            return param_value

            # Strategy 2: Check connected ports (only if no parameter defines the type)
            if self.connector.is_connected():
                connections = self.connector.connections()
                for connected_connector in connections:
                    connected_type = connected_connector.data_type

                    if connected_type != 'any':
                        return connected_type

                    # Recursively resolve
                    if hasattr(connected_connector, 'node') and connected_connector.node:
                        scene = self.scene()
                        if scene and hasattr(scene, '_node_items'):
                            node_item = scene._node_items.get(connected_connector.node.id)
                            if node_item:
                                is_output = connected_connector.is_output()
                                port = node_item.get_port(connected_connector.name, is_output=is_output)
                                if port and port != self:
                                    resolved = port._resolve_data_type(visited)
                                    if resolved != 'any':
                                        return resolved
        else:
            # INPUT PORT: Connected type takes priority (what's actually coming in)

            # Strategy 1: Check connected ports FIRST for inputs
            if self.connector.is_connected():
                connections = self.connector.connections()
                for connected_connector in connections:
                    connected_type = connected_connector.data_type

                    if connected_type != 'any':
                        return connected_type

                    # Recursively resolve the connected output's type
                    if hasattr(connected_connector, 'node') and connected_connector.node:
                        scene = self.scene()
                        if scene and hasattr(scene, '_node_items'):
                            node_item = scene._node_items.get(connected_connector.node.id)
                            if node_item:
                                is_output = connected_connector.is_output()
                                port = node_item.get_port(connected_connector.name, is_output=is_output)
                                if port and port != self:
                                    resolved = port._resolve_data_type(visited)
                                    if resolved != 'any':
                                        return resolved

            # Strategy 2: Check node parameters (only if not connected or connection is also 'any')
            if self.connector.node:
                for param_name in ['type', 'data_type', 'value_type']:
                    param = self.connector.node.parameter(param_name)
                    if param:
                        param_value = param.value()
                        if param_value in self.TYPE_COLORS:
                            return param_value

            # Strategy 3: Check pass-through from output ports (for Display-like nodes)
            if self.connector.node:
                scene = self.scene()
                if scene and hasattr(scene, '_node_items'):
                    node_item = scene._node_items.get(self.connector.node.id)
                    if node_item:
                        for output_name, output_connector in self.connector.node.outputs().items():
                            if output_connector.data_type != 'any':
                                return output_connector.data_type

                            output_port = node_item.get_port(output_name, is_output=True)
                            if output_port and output_port != self:
                                resolved = output_port._resolve_data_type(visited)
                                if resolved != 'any':
                                    return resolved

        # Default: return 'any'
        return 'any'

    def hoverEnterEvent(self, event):
        """Handle hover enter."""
        self._is_hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """Handle hover leave."""
        self._is_hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def get_scene_pos(self) -> QPointF:
        """Get the port position in scene coordinates."""
        return self.scenePos()
