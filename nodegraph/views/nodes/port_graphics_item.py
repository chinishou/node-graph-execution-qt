"""
Port Graphics Item
==================

QGraphicsItem for rendering port (connector) in the network view.
"""

from PySide6.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer
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

        # Cache resolved type to avoid repeated resolution in paint()
        # For concrete types (not 'any'), set cache immediately
        if connector and connector.data_type != 'any':
            self._cached_type = connector.data_type
        else:
            self._cached_type = None

        self._resolution_depth = 0  # Track recursion depth

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)

        # Connect to signals to invalidate cache
        if connector:
            connector.connected_changed.connect(self._invalidate_type_cache)

    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle."""
        r = self.PORT_RADIUS + 2
        return QRectF(-r, -r, 2 * r, 2 * r)

    def _invalidate_type_cache(self):
        """Invalidate the cached type when connections change."""
        # OPTIMIZATION: Skip for ports with concrete types (not 'any')
        # Concrete types won't change regardless of connections, and the cache
        # is already set during initialization. UI updates are handled by
        # NodeGraphicsItem._on_connection_changed triggering scene updates.
        if self.connector.data_type != 'any':
            return

        # Clear cache for 'any' type ports (need to re-resolve from connections)
        self._cached_type = None

        # Request batch update from scene instead of individual update
        scene = self.scene()
        if scene and hasattr(scene, '_schedule_port_update'):
            scene._schedule_port_update(self)
        else:
            # Fallback: Use deferred update to prevent recursion during signal processing
            QTimer.singleShot(0, self.update)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        """Paint the port."""
        painter.setRenderHint(QPainter.Antialiasing)

        # Determine color based on hover state or data type
        if self._is_hovered:
            color = self.HOVER_COLOR
        else:
            # Get the actual data type to use for coloring (with caching)
            if self._cached_type is None:
                self._cached_type = self._resolve_data_type()
            data_type = self._cached_type

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

    def _resolve_data_type(self, visited=None, depth=0) -> str:
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
            depth: Current recursion depth (safety limit)

        Returns:
            The resolved data type string
        """
        # OPTIMIZATION: Use cached result if available and this is a top-level call
        # Only use cache for top-level calls (depth=0) to avoid stale data in recursive chains
        if depth == 0 and self._cached_type is not None:
            return self._cached_type

        # Safety: if scene is modifying connections, use cached type or default
        # This prevents recursion during connection add/remove operations
        scene = self.scene()
        if scene and hasattr(scene, '_is_modifying_connections') and scene._is_modifying_connections:
            return self._cached_type if self._cached_type else self.connector.data_type

        # Safety: prevent excessive recursion
        if depth > 10:
            return 'any'

        if visited is None:
            visited = set()

        # Prevent infinite loops by tracking connectors we've already visited
        connector_id = id(self.connector)
        if connector_id in visited:
            return 'any'
        visited.add(connector_id)

        data_type = self.connector.data_type

        # If not 'any', cache and return the concrete type immediately
        if data_type != 'any':
            if depth == 0:
                self._cached_type = data_type
            return data_type

        # Try node-specific type resolution first (for cross-boundary scenarios)
        if self.connector.node:
            custom_type = self.connector.node.resolve_connector_display_type(
                self.connector.name,
                self.is_output,
                visited
            )
            if custom_type:
                if depth == 0:
                    self._cached_type = custom_type
                return custom_type

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
                            if depth == 0:
                                self._cached_type = param_value
                            return param_value

            # Strategy 2: Check connected ports (only if no parameter defines the type)
            if self.connector.is_connected():
                connections = self.connector.connections()
                for connected_connector in connections:
                    connected_type = connected_connector.data_type

                    if connected_type != 'any':
                        if depth == 0:
                            self._cached_type = connected_type
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
                                    resolved = port._resolve_data_type(visited, depth + 1)
                                    if resolved != 'any':
                                        if depth == 0:
                                            self._cached_type = resolved
                                        return resolved
        else:
            # INPUT PORT: Connected type takes priority (what's actually coming in)

            # Strategy 1: Check connected ports FIRST for inputs
            if self.connector.is_connected():
                connections = self.connector.connections()
                for connected_connector in connections:
                    connected_type = connected_connector.data_type

                    if connected_type != 'any':
                        if depth == 0:
                            self._cached_type = connected_type
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
                                    resolved = port._resolve_data_type(visited, depth + 1)
                                    if resolved != 'any':
                                        if depth == 0:
                                            self._cached_type = resolved
                                        return resolved

            # Strategy 2: Check node parameters (only if not connected or connection is also 'any')
            if self.connector.node:
                for param_name in ['type', 'data_type', 'value_type']:
                    param = self.connector.node.parameter(param_name)
                    if param:
                        param_value = param.value()
                        if param_value in self.TYPE_COLORS:
                            if depth == 0:
                                self._cached_type = param_value
                            return param_value

            # Strategy 3: Check pass-through from output ports (for Display-like nodes)
            # Skip this for nodes that transform types (use transforms_data_type method)
            if self.connector.node:
                # Don't use pass-through for type-converting nodes
                if not self.connector.node.transforms_data_type():
                    scene = self.scene()
                    if scene and hasattr(scene, '_node_items'):
                        node_item = scene._node_items.get(self.connector.node.id)
                        if node_item:
                            for output_name, output_connector in self.connector.node.outputs().items():
                                if output_connector.data_type != 'any':
                                    if depth == 0:
                                        self._cached_type = output_connector.data_type
                                    return output_connector.data_type

                                output_port = node_item.get_port(output_name, is_output=True)
                                if output_port and output_port != self:
                                    resolved = output_port._resolve_data_type(visited, depth + 1)
                                    if resolved != 'any':
                                        if depth == 0:
                                            self._cached_type = resolved
                                        return resolved

        # Default: cache and return 'any'
        if depth == 0:
            self._cached_type = 'any'
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
