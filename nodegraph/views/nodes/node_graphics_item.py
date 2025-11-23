"""
Node Graphics Item
==================

QGraphicsItem for rendering nodes in the network view.
"""

from PySide6.QtWidgets import (
    QGraphicsItem, QGraphicsTextItem, QGraphicsProxyWidget,
    QStyleOptionGraphicsItem, QWidget
)
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath

from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from ...core.models import NodeModel
    from .port_graphics_item import PortGraphicsItem


class NodeGraphicsItem(QGraphicsItem):
    """
    Graphics item for rendering a node.

    Displays the node with:
    - Header bar with node name
    - Input/output ports
    - Houdini-style appearance
    """

    # Node dimensions
    NODE_WIDTH = 160
    HEADER_HEIGHT = 24
    PORT_HEIGHT = 20
    PORT_RADIUS = 6
    CORNER_RADIUS = 4

    # Colors (Houdini-style)
    HEADER_COLOR = QColor(60, 60, 60)
    BODY_COLOR = QColor(45, 45, 45)
    SELECTED_BORDER_COLOR = QColor(255, 180, 50)
    NORMAL_BORDER_COLOR = QColor(30, 30, 30)
    TEXT_COLOR = QColor(220, 220, 220)
    PORT_INPUT_COLOR = QColor(100, 180, 100)
    PORT_OUTPUT_COLOR = QColor(180, 100, 100)

    def __init__(self, node_model: "NodeModel", parent=None):
        super().__init__(parent)

        self.node_model = node_model
        self._ports: Dict[str, "PortGraphicsItem"] = {}
        self._is_updating_connections = False  # Prevent recursion in connection updates

        # Enable features
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)

        # Set position from model
        pos = node_model.position()
        self.setPos(pos[0], pos[1])

        # Create port items
        self._create_ports()

        # Calculate height based on ports
        self._update_height()

        # Connect to model signals
        node_model.position_changed.connect(self._on_position_changed)
        node_model.parameter_changed.connect(self._on_parameter_changed)

    def _create_ports(self):
        """Create port graphics items for all connectors."""
        from .port_graphics_item import PortGraphicsItem

        # Create input ports
        for i, (name, connector) in enumerate(self.node_model.inputs().items()):
            port = PortGraphicsItem(connector, is_output=False, parent=self)
            port.setPos(0, self.HEADER_HEIGHT + i * self.PORT_HEIGHT + self.PORT_HEIGHT / 2)
            self._ports[f"input_{name}"] = port
            # Connect to connector's signal to update colors when connection changes
            connector.connected_changed.connect(self._on_connection_changed)

        # Create output ports
        for i, (name, connector) in enumerate(self.node_model.outputs().items()):
            port = PortGraphicsItem(connector, is_output=True, parent=self)
            port.setPos(self.NODE_WIDTH, self.HEADER_HEIGHT + i * self.PORT_HEIGHT + self.PORT_HEIGHT / 2)
            self._ports[f"output_{name}"] = port
            # Connect to connector's signal to update colors when connection changes
            connector.connected_changed.connect(self._on_connection_changed)

    def _update_height(self):
        """Update node height based on number of ports."""
        num_inputs = len(self.node_model.inputs())
        num_outputs = len(self.node_model.outputs())
        max_ports = max(num_inputs, num_outputs, 1)
        self._height = self.HEADER_HEIGHT + max_ports * self.PORT_HEIGHT

    def get_port(self, port_name: str, is_output: bool) -> Optional["PortGraphicsItem"]:
        """Get a port graphics item by name."""
        key = f"{'output' if is_output else 'input'}_{port_name}"
        return self._ports.get(key)

    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of the node."""
        return QRectF(0, 0, self.NODE_WIDTH, self._height)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        """Paint the node."""
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw body
        body_rect = QRectF(0, 0, self.NODE_WIDTH, self._height)
        path = QPainterPath()
        path.addRoundedRect(body_rect, self.CORNER_RADIUS, self.CORNER_RADIUS)

        painter.fillPath(path, QBrush(self.BODY_COLOR))

        # Draw header
        header_rect = QRectF(0, 0, self.NODE_WIDTH, self.HEADER_HEIGHT)
        header_path = QPainterPath()
        header_path.addRoundedRect(header_rect, self.CORNER_RADIUS, self.CORNER_RADIUS)

        # Custom color if set
        header_color = self.HEADER_COLOR
        if self.node_model.color:
            header_color = QColor(self.node_model.color)

        painter.fillPath(header_path, QBrush(header_color))

        # Draw border
        border_color = self.SELECTED_BORDER_COLOR if self.isSelected() else self.NORMAL_BORDER_COLOR
        painter.setPen(QPen(border_color, 2 if self.isSelected() else 1))
        painter.drawPath(path)

        # Draw node name
        painter.setPen(QPen(self.TEXT_COLOR))
        font = QFont("Sans", 9)
        font.setBold(True)
        painter.setFont(font)

        text_rect = QRectF(8, 0, self.NODE_WIDTH - 16, self.HEADER_HEIGHT)
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, self.node_model.name)

        # Draw port labels
        font.setBold(False)
        font.setPointSize(8)
        painter.setFont(font)

        # Import port color mapping
        from .port_graphics_item import PortGraphicsItem

        # Input labels
        for i, (name, connector) in enumerate(self.node_model.inputs().items()):
            y = self.HEADER_HEIGHT + i * self.PORT_HEIGHT
            label = connector.label or name

            # Get resolved data type from the port (uses recursive resolution)
            port = self.get_port(name, is_output=False)
            if port:
                data_type = port._resolve_data_type(visited=None, depth=0)
            else:
                data_type = connector.data_type

            if data_type in PortGraphicsItem.TYPE_COLORS:
                label_color = PortGraphicsItem.TYPE_COLORS[data_type]
            else:
                label_color = PortGraphicsItem.CUSTOM_TYPE_COLOR

            painter.setPen(QPen(label_color))
            text_rect = QRectF(12, y, self.NODE_WIDTH / 2 - 16, self.PORT_HEIGHT)
            painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, label)

        # Output labels
        for i, (name, connector) in enumerate(self.node_model.outputs().items()):
            y = self.HEADER_HEIGHT + i * self.PORT_HEIGHT
            label = connector.label or name

            # Get resolved data type from the port (uses recursive resolution)
            port = self.get_port(name, is_output=True)
            if port:
                data_type = port._resolve_data_type(visited=None, depth=0)
            else:
                data_type = connector.data_type

            if data_type in PortGraphicsItem.TYPE_COLORS:
                label_color = PortGraphicsItem.TYPE_COLORS[data_type]
            else:
                label_color = PortGraphicsItem.CUSTOM_TYPE_COLOR

            painter.setPen(QPen(label_color))
            text_rect = QRectF(self.NODE_WIDTH / 2, y, self.NODE_WIDTH / 2 - 12, self.PORT_HEIGHT)
            painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignRight, label)

    def itemChange(self, change, value):
        """Handle item changes."""
        if change == QGraphicsItem.ItemPositionHasChanged:
            # Update model position
            pos = self.pos()
            self.node_model.set_position(pos.x(), pos.y(), emit_signal=False)

            # Update connected edges
            scene = self.scene()
            if scene and hasattr(scene, 'update_connections'):
                scene.update_connections(self)

        return super().itemChange(change, value)

    def _on_position_changed(self, x: float, y: float):
        """Handle position change from model."""
        self.setPos(x, y)

    def _on_parameter_changed(self):
        """Handle parameter change from model."""
        # Update the node to reflect new colors
        self.update()
        # Update all ports (important for Math/Convert nodes where type changes)
        for port in self._ports.values():
            port.update()
        # Update all connections involving this node
        scene = self.scene()
        if scene and hasattr(scene, '_connection_items'):
            for conn_item in scene._connection_items:
                if (conn_item.source_port and conn_item.source_port.parentItem() == self) or \
                   (conn_item.target_port and conn_item.target_port.parentItem() == self):
                    conn_item.update()

    def _on_connection_changed(self):
        """Handle connector connection state change."""
        # Prevent recursion: if we're already updating connections, skip this call
        if self._is_updating_connections:
            return

        try:
            self._is_updating_connections = True

            # Update the node to reflect new colors
            self.update()
            # Update all ports
            for port in self._ports.values():
                port.update()
            # Update all connections involving this node
            scene = self.scene()
            if scene and hasattr(scene, '_connection_items'):
                for conn_item in scene._connection_items:
                    if (conn_item.source_port and conn_item.source_port.parentItem() == self) or \
                       (conn_item.target_port and conn_item.target_port.parentItem() == self):
                        conn_item.update()
        finally:
            self._is_updating_connections = False

    def mouseDoubleClickEvent(self, event):
        """Handle double-click to execute node."""
        if self.node_model.execute():
            # Visual feedback
            self.update()
        super().mouseDoubleClickEvent(event)

