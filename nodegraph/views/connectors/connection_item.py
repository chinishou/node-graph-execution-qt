"""
Connection Item
===============

QGraphicsItem for rendering connections between ports.
"""

from PySide6.QtWidgets import QGraphicsPathItem, QStyleOptionGraphicsItem, QWidget, QStyle
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..nodes.port_graphics_item import PortGraphicsItem


class ConnectionItem(QGraphicsPathItem):
    """
    Graphics item for rendering a connection between two ports.

    Uses cubic Bezier curves for smooth connections.
    """

    # Colors
    NORMAL_COLOR = QColor(180, 180, 180)
    SELECTED_COLOR = QColor(255, 200, 50)
    TEMP_COLOR = QColor(150, 150, 150, 150)

    def __init__(
        self,
        source_port: Optional["PortGraphicsItem"] = None,
        target_port: Optional["PortGraphicsItem"] = None,
        parent=None
    ):
        super().__init__(parent)

        self.source_port = source_port
        self.target_port = target_port
        self._temp_end_pos: Optional[QPointF] = None

        # Style
        self.setFlag(QGraphicsPathItem.ItemIsSelectable, True)
        self.setPen(QPen(self.NORMAL_COLOR, 2))

        self.update_path()

    def set_source_port(self, port: "PortGraphicsItem"):
        """Set the source port."""
        self.source_port = port
        self.update_path()

    def set_target_port(self, port: "PortGraphicsItem"):
        """Set the target port."""
        self.target_port = port
        self._temp_end_pos = None
        self.update_path()

    def set_temp_end_pos(self, pos: QPointF):
        """Set temporary end position for dragging."""
        self._temp_end_pos = pos
        self.update_path()

    def update_path(self):
        """Update the connection path."""
        if not self.source_port:
            return

        # Get start position
        start_pos = self.source_port.get_scene_pos()

        # Get end position
        if self.target_port:
            end_pos = self.target_port.get_scene_pos()
        elif self._temp_end_pos:
            end_pos = self._temp_end_pos
        else:
            return

        # Determine if source is output (going right) or input (going left)
        source_is_output = self.source_port.is_output

        # Create path
        path = QPainterPath()
        path.moveTo(start_pos)

        # Calculate control points for cubic Bezier
        dx = end_pos.x() - start_pos.x()
        dy = end_pos.y() - start_pos.y()

        # Horizontal offset for control points
        ctrl_offset = min(abs(dx) * 0.5, 100)
        ctrl_offset = max(ctrl_offset, 30)

        # Adjust control point direction based on port type
        if source_is_output:
            # Output port: curve goes right then to target
            ctrl1 = QPointF(start_pos.x() + ctrl_offset, start_pos.y())
            ctrl2 = QPointF(end_pos.x() - ctrl_offset, end_pos.y())
        else:
            # Input port: curve goes left then to target
            ctrl1 = QPointF(start_pos.x() - ctrl_offset, start_pos.y())
            ctrl2 = QPointF(end_pos.x() + ctrl_offset, end_pos.y())

        path.cubicTo(ctrl1, ctrl2, end_pos)

        self.setPath(path)

    def shape(self):
        """Return a more precise shape for mouse interaction."""
        # Create a stroker to make a clickable area around the path
        from PySide6.QtGui import QPainterPathStroker
        stroker = QPainterPathStroker()
        stroker.setWidth(8)  # Clickable width
        return stroker.createStroke(self.path())

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        """Paint the connection."""
        painter.setRenderHint(QPainter.Antialiasing)

        # Determine color
        if self._temp_end_pos and not self.target_port:
            color = self.TEMP_COLOR
        elif self.isSelected():
            color = self.SELECTED_COLOR
        else:
            # Get color based on data type
            color = self._get_connection_color()

        pen = QPen(color, 2)
        pen.setCapStyle(Qt.RoundCap)
        self.setPen(pen)

        # Disable selection rectangle by modifying the option
        option.state &= ~QStyle.State_Selected

        super().paint(painter, option, widget)

    def _get_connection_color(self) -> QColor:
        """Get the connection color based on data type."""
        from ..nodes.port_graphics_item import PortGraphicsItem

        if not self.source_port or not self.target_port:
            return self.NORMAL_COLOR

        # Get data types from both ports
        source_type = self.source_port.connector.data_type
        target_type = self.target_port.connector.data_type

        # Determine the actual data type being transmitted
        data_type = None

        if source_type != 'any' and target_type != 'any':
            # Both are typed, use source type (they should match due to validation)
            data_type = source_type
        elif source_type != 'any':
            # Source is typed, target is 'any'
            data_type = source_type
        elif target_type != 'any':
            # Target is typed, source is 'any'
            data_type = target_type
        else:
            # Both are 'any' - try to determine from node parameters or connections
            source_connector = self.source_port.connector
            target_connector = self.target_port.connector

            # Check if source node has type parameters (for Math/Convert nodes)
            if source_connector.node:
                # For Math nodes, check 'type' parameter
                type_param = source_connector.node.parameter('type')
                if type_param:
                    param_value = type_param.value()
                    if param_value in PortGraphicsItem.TYPE_COLORS:
                        data_type = param_value

                # For Convert node output, check 'output_type' parameter
                if data_type is None and self.source_port.is_output:
                    output_type_param = source_connector.node.parameter('output_type')
                    if output_type_param:
                        param_value = output_type_param.value()
                        if param_value in PortGraphicsItem.TYPE_COLORS:
                            data_type = param_value

            # Check if target node has type parameters
            if data_type is None and target_connector.node:
                type_param = target_connector.node.parameter('type')
                if type_param:
                    param_value = type_param.value()
                    if param_value in PortGraphicsItem.TYPE_COLORS:
                        data_type = param_value

            # Check if source has other connections that might determine its type
            if data_type is None and source_connector.is_connected():
                connections = source_connector.connections()
                for conn in connections:
                    if conn.data_type != 'any':
                        data_type = conn.data_type
                        break

            # Check if target has other connections that might determine its type
            if data_type is None and target_connector.is_connected():
                connections = target_connector.connections()
                for conn in connections:
                    if conn.data_type != 'any':
                        data_type = conn.data_type
                        break

            # If still 'any', just use gray
            if data_type is None:
                data_type = 'any'

        # Get color based on data type
        if data_type in PortGraphicsItem.TYPE_COLORS:
            return PortGraphicsItem.TYPE_COLORS[data_type]
        else:
            # Custom type - use purple
            return PortGraphicsItem.CUSTOM_TYPE_COLOR


class TempConnectionItem(ConnectionItem):
    """Temporary connection item used during dragging."""

    def __init__(self, source_port: "PortGraphicsItem", parent=None):
        super().__init__(source_port=source_port, parent=parent)
        self.setPen(QPen(self.TEMP_COLOR, 2, Qt.DashLine))
