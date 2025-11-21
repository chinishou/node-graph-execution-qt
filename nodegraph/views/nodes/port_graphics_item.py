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
            data_type = self.connector.data_type

            # If this is 'any' type, try to determine actual type
            if data_type == 'any':
                # First, check if connected and use connected type
                if self.connector.is_connected():
                    connections = self.connector.connections()
                    if connections:
                        # Get the data type from the first connected port
                        connected_type = connections[0].data_type
                        # If the connected port is also 'any', keep checking
                        if connected_type != 'any':
                            data_type = connected_type

                # If still 'any', check if node has a 'type' parameter (for Math/Convert nodes)
                if data_type == 'any' and self.connector.node:
                    type_param = self.connector.node.parameter('type')
                    if type_param:
                        param_value = type_param.value()
                        # Use the parameter value as the data type
                        if param_value in self.TYPE_COLORS:
                            data_type = param_value

                    # For Convert node, check 'output_type' parameter
                    output_type_param = self.connector.node.parameter('output_type')
                    if output_type_param and self.is_output:
                        param_value = output_type_param.value()
                        if param_value in self.TYPE_COLORS:
                            data_type = param_value

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
