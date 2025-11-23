"""
Network Scene
=============

QGraphicsScene for the node network editor.
"""

from PySide6.QtWidgets import QGraphicsScene, QGraphicsItem
from PySide6.QtCore import Qt, QPointF, Signal, QTimer
from PySide6.QtGui import QColor, QPen, QBrush

from typing import TYPE_CHECKING, Dict, Optional, List, Set
from uuid import UUID

if TYPE_CHECKING:
    from ...core.models import NetworkModel, NodeModel, ConnectorModel
    from ..nodes.node_graphics_item import NodeGraphicsItem
    from ..nodes.port_graphics_item import PortGraphicsItem
    from ..connectors.connection_item import ConnectionItem
    from ..notes.sticky_note_item import StickyNoteItem


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
        self._sticky_notes: Dict[UUID, "StickyNoteItem"] = {}
        self._temp_connection: Optional["ConnectionItem"] = None
        self._dragging_port: Optional["PortGraphicsItem"] = None

        # Deferred update management to prevent recursion
        self._pending_updates: Set["ConnectionItem"] = set()
        self._update_timer: Optional[QTimer] = None

        # Global flag to prevent type resolution during connection modifications
        self._is_modifying_connections = False

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
        self._sticky_notes.clear()

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

            # Remove associated connections from scene
            connections_to_remove = [
                conn for conn in self._connection_items
                if self._connection_involves_node(conn, node)
            ]

            for conn in connections_to_remove:
                self.removeItem(conn)
                self._connection_items.remove(conn)

    def _connection_involves_node(self, connection: "ConnectionItem", node: "NodeModel") -> bool:
        """Check if a connection involves a node."""
        if connection.source_port and connection.source_port.connector.node == node:
            return True
        if connection.target_port and connection.target_port.connector.node == node:
            return True
        return False

    def _on_connection_added(self, source_conn: "ConnectorModel", target_conn: "ConnectorModel"):
        """Handle connection added to model."""
        # Debug logging
        if hasattr(source_conn, 'node') and hasattr(target_conn, 'node'):
            print(f"[Scene] _on_connection_added called: {source_conn.node.name}.{source_conn.name} -> {target_conn.node.name}.{target_conn.name}")

        # Set flag to prevent type resolution during modification
        was_modifying = self._is_modifying_connections
        self._is_modifying_connections = True
        try:
            print(f"[Scene] Before create: {len(self._connection_items)} items in list")
            self._create_connection_item(source_conn, target_conn)
            print(f"[Scene] After create: {len(self._connection_items)} items in list")
        finally:
            # Only reset if we set it
            if not was_modifying:
                self._is_modifying_connections = False

    def _on_connection_removed(self, source_conn: "ConnectorModel", target_conn: "ConnectorModel"):
        """Handle connection removed from model."""
        # Debug logging
        if hasattr(source_conn, 'node') and hasattr(target_conn, 'node'):
            print(f"[Scene] _on_connection_removed called: {source_conn.node.name}.{source_conn.name} -> {target_conn.node.name}.{target_conn.name}")

        # Set flag to prevent type resolution during modification
        was_modifying = self._is_modifying_connections
        self._is_modifying_connections = True
        try:
            # Debug: list all current connections
            print(f"[Scene] Current connection items ({len(self._connection_items)}):")
            for i, conn in enumerate(self._connection_items):
                try:
                    if conn.source_port and conn.target_port:
                        src = conn.source_port.connector
                        tgt = conn.target_port.connector
                        print(f"  [{i}] {src.node.name}.{src.name} -> {tgt.node.name}.{tgt.name}")
                        print(f"      source_conn match: {src == source_conn} (id: {id(src)} vs {id(source_conn)})")
                        print(f"      target_conn match: {tgt == target_conn} (id: {id(tgt)} vs {id(target_conn)})")
                    else:
                        print(f"  [{i}] <invalid connection: source_port={conn.source_port}, target_port={conn.target_port}>")
                except Exception as e:
                    print(f"  [{i}] <ERROR accessing connection: {type(e).__name__}: {e}>")

            # Find and remove the connection item
            found = False
            for conn in self._connection_items[:]:
                try:
                    if (conn.source_port and conn.target_port and
                        conn.source_port.connector == source_conn and
                        conn.target_port.connector == target_conn):
                        print(f"[Scene] ✓ Found! Removing connection item from scene")
                        self.removeItem(conn)
                        self._connection_items.remove(conn)
                        found = True
                        break
                except Exception as e:
                    # Skip this connection if comparison fails (e.g., RecursionError during __eq__)
                    print(f"[Scene] ! Skipping connection due to comparison error: {type(e).__name__}")
                    continue
            if not found:
                print(f"[Scene] ✗ WARNING: Connection item not found in _connection_items!")
        finally:
            # Only reset if we set it
            if not was_modifying:
                self._is_modifying_connections = False

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

        # Connect to connector signals to update connection color when types change
        # Use deferred update to prevent recursion
        source_conn.connected_changed.connect(lambda: self._schedule_connection_update(conn_item))
        target_conn.connected_changed.connect(lambda: self._schedule_connection_update(conn_item))

    def update_connections(self, node_item: "NodeGraphicsItem"):
        """Update all connections involving a node."""
        for conn in self._connection_items:
            if conn.source_port and conn.source_port.parentItem() == node_item:
                conn.update_path()
            elif conn.target_port and conn.target_port.parentItem() == node_item:
                conn.update_path()

    def _schedule_connection_update(self, conn_item: "ConnectionItem"):
        """
        Schedule a deferred update for a connection item.

        This prevents recursion by batching updates and processing them
        in the next event loop iteration, after all signals have been emitted.
        """
        self._pending_updates.add(conn_item)

        # Create timer if not exists, or restart it
        if self._update_timer is None:
            self._update_timer = QTimer()
            self._update_timer.setSingleShot(True)
            self._update_timer.timeout.connect(self._process_pending_updates)

        # Schedule for next event loop (0ms delay)
        if not self._update_timer.isActive():
            self._update_timer.start(0)

    def _process_pending_updates(self):
        """Process all pending connection updates."""
        # Take a snapshot and clear the pending set
        items_to_update = list(self._pending_updates)
        self._pending_updates.clear()

        # Update all pending items
        for conn_item in items_to_update:
            # Check if item still exists in scene
            if conn_item in self._connection_items:
                conn_item.update()

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

    def create_connection(self, output_port: "PortGraphicsItem", input_port: "PortGraphicsItem") -> bool:
        """Create a connection between two ports."""
        if not output_port or not input_port:
            return False

        # Validate connection
        if output_port == input_port:
            return False

        if output_port.connector.node == input_port.connector.node:
            return False

        if not output_port.is_output or input_port.is_output:
            return False

        # Create connection in model
        output_conn = output_port.connector
        input_conn = input_port.connector

        success = self.network_model.connect(
            output_conn.node.id, output_conn.name,
            input_conn.node.id, input_conn.name
        )

        return success

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
            from ..notes.sticky_note_item import StickyNoteItem

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
            elif isinstance(item, StickyNoteItem):
                self.remove_sticky_note(item.note_id)

    def add_sticky_note(self, position: QPointF = None, text: str = "",
                       color: str = 'yellow', width: float = None,
                       height: float = None) -> "StickyNoteItem":
        """Add a new sticky note to the scene."""
        from ..notes.sticky_note_item import StickyNoteItem

        if position is None:
            # Default to center of view
            position = QPointF(0, 0)

        note = StickyNoteItem(
            position=position,
            text=text,
            color=color,
            width=width,
            height=height
        )

        self.addItem(note)
        self._sticky_notes[note.note_id] = note

        return note

    def remove_sticky_note(self, note_id: UUID):
        """Remove a sticky note from the scene."""
        if note_id in self._sticky_notes:
            note = self._sticky_notes.pop(note_id)
            self.removeItem(note)

    def get_sticky_notes(self) -> List["StickyNoteItem"]:
        """Get all sticky notes in the scene."""
        return list(self._sticky_notes.values())

    def clear_sticky_notes(self):
        """Clear all sticky notes from the scene."""
        for note in list(self._sticky_notes.values()):
            self.removeItem(note)
        self._sticky_notes.clear()
