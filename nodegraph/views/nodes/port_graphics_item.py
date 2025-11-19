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

    # Colors
    INPUT_COLOR = QColor(100, 180, 100)
    OUTPUT_COLOR = QColor(180, 100, 100)
    CONNECTED_COLOR = QColor(255, 200, 50)
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

        # Determine color
        if self._is_hovered:
            color = self.HOVER_COLOR
        elif self.connector.is_connected():
            color = self.CONNECTED_COLOR
        elif self.is_output:
            color = self.OUTPUT_COLOR
        else:
            color = self.INPUT_COLOR

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
