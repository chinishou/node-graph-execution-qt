"""
Connection Item
===============

QGraphicsItem for rendering connections between ports.
"""

from PySide6.QtWidgets import QGraphicsPathItem, QStyleOptionGraphicsItem, QWidget
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

        # Create path
        path = QPainterPath()
        path.moveTo(start_pos)

        # Calculate control points for cubic Bezier
        dx = end_pos.x() - start_pos.x()
        dy = end_pos.y() - start_pos.y()

        # Horizontal offset for control points
        ctrl_offset = min(abs(dx) * 0.5, 100)
        ctrl_offset = max(ctrl_offset, 30)

        ctrl1 = QPointF(start_pos.x() + ctrl_offset, start_pos.y())
        ctrl2 = QPointF(end_pos.x() - ctrl_offset, end_pos.y())

        path.cubicTo(ctrl1, ctrl2, end_pos)

        self.setPath(path)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        """Paint the connection."""
        painter.setRenderHint(QPainter.Antialiasing)

        # Determine color
        if self._temp_end_pos and not self.target_port:
            color = self.TEMP_COLOR
        elif self.isSelected():
            color = self.SELECTED_COLOR
        else:
            color = self.NORMAL_COLOR

        pen = QPen(color, 2)
        pen.setCapStyle(Qt.RoundCap)
        self.setPen(pen)

        super().paint(painter, option, widget)


class TempConnectionItem(ConnectionItem):
    """Temporary connection item used during dragging."""

    def __init__(self, source_port: "PortGraphicsItem", parent=None):
        super().__init__(source_port=source_port, parent=parent)
        self.setPen(QPen(self.TEMP_COLOR, 2, Qt.DashLine))
