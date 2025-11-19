"""
Network Scene
=============

QGraphicsScene for the node network editor.
"""

from PySide6.QtWidgets import QGraphicsScene, QGraphicsItem
from PySide6.QtCore import Qt, QPointF, Signal
from PySide6.QtGui import QColor, QPen, QBrush

from typing import TYPE_CHECKING, Dict, Optional, List
from uuid import UUID

if TYPE_CHECKING:
    from ...core.models import NetworkModel, NodeModel, ConnectorModel
    from ..nodes.node_graphics_item import NodeGraphicsItem
    from ..nodes.port_graphics_item import PortGraphicsItem
    from ..connectors.connection_item import ConnectionItem


class NetworkScene(QGraphicsScene):
    """
    Scene for the node network editor.

    Manages:
    - Node graphics items
    - Connection items
    - Drag-to-connect behavior
    """

    # Signals
    node_selected = Signal(object)  # NodeModel or None
    connection_created = Signal(object, object)  # source_connector, target_connector

    # Grid settings
    GRID_SIZE = 20
    GRID_COLOR = QColor(50, 50, 50)
    BACKGROUND_COLOR = QColor(38, 38, 38)

    def __init__(self, network_model: "NetworkModel" = None, parent=None):
        super().__init__(parent)

        self.network_model = network_model
        self._node_items: Dict[UUID, "NodeGraphicsItem"] = {}
        self._connection_items: List["ConnectionItem"] = []
        self._temp_connection: Optional["ConnectionItem"] = None
        self._dragging_port: Optional["PortGraphicsItem"] = None

        # Set background
        self.setBackgroundBrush(QBrush(self.BACKGROUND_COLOR))

        # Connect to model signals if provided
        if network_model:
            self._setup_model_connections()
            self._create_items_from_model()

    def set_network_model(self, network_model: "NetworkModel"):
        """Set the network model and rebuild the scene."""
        # Clear existing items
        self.clear()
        self._node_items.clear()
        self._connection_items.clear()

        self.network_model = network_model

        if network_model:
            self._setup_model_connections()
            self._create_items_from_model()

    def _setup_model_connections(self):
        """Connect to network model signals."""
        self.network_model.node_added.connect(self._on_node_added)
        self.network_model.node_removed.connect(self._on_node_removed)
        self.network_model.connection_added.connect(self._on_connection_added)
        self.network_model.connection_removed.connect(self._on_connection_removed)

    def _create_items_from_model(self):
        """Create graphics items from the network model."""
        from ..nodes.node_graphics_item import NodeGraphicsItem
        from ..connectors.connection_item import ConnectionItem

        # Create node items
        for node in self.network_model.nodes():
            item = NodeGraphicsItem(node)
            self.addItem(item)
            self._node_items[node.id] = item

        # Create connection items
        for source_conn, target_conn in self.network_model.connector_pairs():
            self._create_connection_item(source_conn, target_conn)

    def _on_node_added(self, node: "NodeModel"):
        """Handle node added to model."""
        from ..nodes.node_graphics_item import NodeGraphicsItem

        item = NodeGraphicsItem(node)
        self.addItem(item)
        self._node_items[node.id] = item

    def _on_node_removed(self, node: "NodeModel"):
        """Handle node removed from model."""
        if node.id in self._node_items:
            item = self._node_items.pop(node.id)
            self.removeItem(item)

            # Remove associated connections
            self._connection_items = [
                conn for conn in self._connection_items
                if not self._connection_involves_node(conn, node)
            ]

    def _connection_involves_node(self, connection: "ConnectionItem", node: "NodeModel") -> bool:
        """Check if a connection involves a node."""
        if connection.source_port and connection.source_port.connector.node == node:
            return True
        if connection.target_port and connection.target_port.connector.node == node:
            return True
        return False

    def _on_connection_added(self, source_conn: "ConnectorModel", target_conn: "ConnectorModel"):
        """Handle connection added to model."""
        self._create_connection_item(source_conn, target_conn)

    def _on_connection_removed(self, source_conn: "ConnectorModel", target_conn: "ConnectorModel"):
        """Handle connection removed from model."""
        # Find and remove the connection item
        for conn in self._connection_items[:]:
            if (conn.source_port and conn.target_port and
                conn.source_port.connector == source_conn and
                conn.target_port.connector == target_conn):
                self.removeItem(conn)
                self._connection_items.remove(conn)
                break

    def _create_connection_item(self, source_conn: "ConnectorModel", target_conn: "ConnectorModel"):
        """Create a connection item between two connectors."""
        from ..connectors.connection_item import ConnectionItem

        # Find port items
        source_node = source_conn.node
        target_node = target_conn.node

        if not source_node or not target_node:
            return

        source_node_item = self._node_items.get(source_node.id)
        target_node_item = self._node_items.get(target_node.id)

        if not source_node_item or not target_node_item:
            return

        source_port = source_node_item.get_port(source_conn.name, is_output=True)
        target_port = target_node_item.get_port(target_conn.name, is_output=False)

        if not source_port or not target_port:
            return

        # Create connection item
        conn_item = ConnectionItem(source_port, target_port)
        self.addItem(conn_item)
        self._connection_items.append(conn_item)

    def update_connections(self, node_item: "NodeGraphicsItem"):
        """Update all connections involving a node."""
        for conn in self._connection_items:
            if conn.source_port and conn.source_port.parentItem() == node_item:
                conn.update_path()
            elif conn.target_port and conn.target_port.parentItem() == node_item:
                conn.update_path()

    def get_node_item(self, node_id: UUID) -> Optional["NodeGraphicsItem"]:
        """Get node graphics item by node ID."""
        return self._node_items.get(node_id)

    def get_port_at_pos(self, pos: QPointF) -> Optional["PortGraphicsItem"]:
        """Get port at a scene position."""
        from ..nodes.port_graphics_item import PortGraphicsItem

        items = self.items(pos)
        for item in items:
            if isinstance(item, PortGraphicsItem):
                return item
        return None

    def start_connection_drag(self, port: "PortGraphicsItem"):
        """Start dragging a connection from a port."""
        from ..connectors.connection_item import TempConnectionItem

        self._dragging_port = port
        self._temp_connection = TempConnectionItem(port)
        self.addItem(self._temp_connection)

    def update_connection_drag(self, pos: QPointF):
        """Update the temporary connection during drag."""
        if self._temp_connection:
            self._temp_connection.set_temp_end_pos(pos)

    def finish_connection_drag(self, end_pos: QPointF) -> bool:
        """Finish the connection drag and create connection if valid."""
        if not self._temp_connection or not self._dragging_port:
            self._cleanup_drag()
            return False

        # Find port at end position
        target_port = self.get_port_at_pos(end_pos)

        if target_port and target_port != self._dragging_port:
            # Try to create connection in model
            source_conn = self._dragging_port.connector
            target_conn = target_port.connector

            # Determine which is output and which is input
            if source_conn.is_output() and target_conn.is_input():
                success = self.network_model.connect(
                    source_conn.node.id, source_conn.name,
                    target_conn.node.id, target_conn.name
                )
            elif source_conn.is_input() and target_conn.is_output():
                success = self.network_model.connect(
                    target_conn.node.id, target_conn.name,
                    source_conn.node.id, source_conn.name
                )
            else:
                success = False

            self._cleanup_drag()
            return success

        self._cleanup_drag()
        return False

    def _cleanup_drag(self):
        """Clean up after connection drag."""
        if self._temp_connection:
            self.removeItem(self._temp_connection)
            self._temp_connection = None
        self._dragging_port = None

    def cancel_connection_drag(self):
        """Cancel the current connection drag."""
        self._cleanup_drag()

    def drawBackground(self, painter, rect):
        """Draw the background with grid."""
        super().drawBackground(painter, rect)

        # Draw grid
        painter.setPen(QPen(self.GRID_COLOR, 0.5))

        left = int(rect.left()) - (int(rect.left()) % self.GRID_SIZE)
        top = int(rect.top()) - (int(rect.top()) % self.GRID_SIZE)

        lines = []
        x = left
        while x < rect.right():
            lines.append((x, rect.top(), x, rect.bottom()))
            x += self.GRID_SIZE

        y = top
        while y < rect.bottom():
            lines.append((rect.left(), y, rect.right(), y))
            y += self.GRID_SIZE

        for line in lines:
            painter.drawLine(line[0], line[1], line[2], line[3])

    def delete_selected(self):
        """Delete selected items."""
        selected = self.selectedItems()

        for item in selected:
            from ..nodes.node_graphics_item import NodeGraphicsItem
            from ..connectors.connection_item import ConnectionItem

            if isinstance(item, NodeGraphicsItem):
                self.network_model.remove_node(item.node_model.id)
            elif isinstance(item, ConnectionItem):
                if item.source_port and item.target_port:
                    source_conn = item.source_port.connector
                    target_conn = item.target_port.connector
                    self.network_model.disconnect(
                        source_conn.node.id, source_conn.name,
                        target_conn.node.id, target_conn.name
                    )
