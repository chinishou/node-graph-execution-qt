"""
Network View
============

QGraphicsView for the node network editor.
"""

from PySide6.QtWidgets import (
    QGraphicsView, QMenu, QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt, QPointF, Signal
from PySide6.QtGui import QPainter, QWheelEvent, QMouseEvent, QKeyEvent

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ...core.models import NetworkModel
    from ...core.registry import NodeRegistry
    from .network_scene import NetworkScene
    from ..nodes.port_graphics_item import PortGraphicsItem


class NetworkView(QGraphicsView):
    """
    View for the node network editor.

    Provides:
    - Pan/zoom navigation
    - Context menu for node creation
    - Tab key for node palette
    - Connection dragging
    """

    # Signals
    node_selected = Signal(object)  # NodeModel or None

    # Zoom settings
    ZOOM_MIN = 0.1
    ZOOM_MAX = 4.0
    ZOOM_STEP = 1.15

    def __init__(self, parent=None):
        super().__init__(parent)

        self._scene: Optional["NetworkScene"] = None
        self._panning = False
        self._last_pan_pos = QPointF()
        self._connecting = False
        self._zoom_level = 1.0

        # Setup view
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.RubberBandDrag)

        # Enable focus for key events
        self.setFocusPolicy(Qt.StrongFocus)

    def set_scene(self, scene: "NetworkScene"):
        """Set the network scene."""
        self._scene = scene
        self.setScene(scene)

        # Connect scene signals
        scene.selectionChanged.connect(self._on_selection_changed)

    def _on_selection_changed(self):
        """Handle selection change in scene."""
        selected = self._scene.selectedItems()

        from ..nodes.node_graphics_item import NodeGraphicsItem

        # Find selected node
        node_model = None
        for item in selected:
            if isinstance(item, NodeGraphicsItem):
                node_model = item.node_model
                break

        self.node_selected.emit(node_model)

    # Navigation

    def wheelEvent(self, event: QWheelEvent):
        """Handle zoom with mouse wheel."""
        if event.angleDelta().y() > 0:
            zoom_factor = self.ZOOM_STEP
        else:
            zoom_factor = 1.0 / self.ZOOM_STEP

        new_zoom = self._zoom_level * zoom_factor

        if self.ZOOM_MIN <= new_zoom <= self.ZOOM_MAX:
            self._zoom_level = new_zoom
            self.scale(zoom_factor, zoom_factor)

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press."""
        if event.button() == Qt.MiddleButton:
            # Start panning
            self._panning = True
            self._last_pan_pos = event.position()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return

        if event.button() == Qt.LeftButton:
            # Check if clicking on a port
            scene_pos = self.mapToScene(event.position().toPoint())
            port = self._scene.get_port_at_pos(scene_pos) if self._scene else None

            if port:
                # Start connection drag
                self._connecting = True
                self._scene.start_connection_drag(port)
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move."""
        if self._panning:
            # Pan view
            delta = event.position() - self._last_pan_pos
            self._last_pan_pos = event.position()

            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(delta.x())
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(delta.y())
            )
            event.accept()
            return

        if self._connecting and self._scene:
            # Update connection drag
            scene_pos = self.mapToScene(event.position().toPoint())
            self._scene.update_connection_drag(scene_pos)
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release."""
        if event.button() == Qt.MiddleButton and self._panning:
            self._panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return

        if event.button() == Qt.LeftButton and self._connecting:
            # Finish connection drag
            scene_pos = self.mapToScene(event.position().toPoint())
            if self._scene:
                self._scene.finish_connection_drag(scene_pos)
            self._connecting = False
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press."""
        if event.key() == Qt.Key_Tab:
            # Show node palette at cursor position
            cursor_pos = self.mapFromGlobal(self.cursor().pos())
            scene_pos = self.mapToScene(cursor_pos)
            self._show_node_menu(self.mapToGlobal(cursor_pos), scene_pos)
            event.accept()
            return

        if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            # Delete selected items
            if self._scene:
                self._scene.delete_selected()
            event.accept()
            return

        if event.key() == Qt.Key_F:
            # Frame selected or all
            self.frame_selection()
            event.accept()
            return

        super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        """Show context menu on right-click."""
        scene_pos = self.mapToScene(event.pos())

        # Check if clicking on empty space
        item = self.itemAt(event.pos())
        if item is None:
            self._show_node_menu(event.globalPos(), scene_pos)
        else:
            # Show item-specific menu
            super().contextMenuEvent(event)

    def _show_node_menu(self, global_pos, scene_pos: QPointF):
        """Show the node creation menu."""
        from ...core.registry import NodeRegistry

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #3c3c3c;
                color: #dcdcdc;
                border: 1px solid #5c5c5c;
            }
            QMenu::item:selected {
                background-color: #505050;
            }
            QMenu::separator {
                height: 1px;
                background: #5c5c5c;
            }
        """)

        # Group nodes by category
        categories = NodeRegistry.get_categories()

        for category in categories:
            category_menu = menu.addMenu(category)
            nodes = NodeRegistry.get_nodes_by_category(category)

            for node_type, node_class in nodes.items():
                action = category_menu.addAction(node_type)
                action.setData((node_type, scene_pos))

        # Connect action
        menu.triggered.connect(self._on_node_menu_action)
        menu.exec(global_pos)

    def _on_node_menu_action(self, action):
        """Handle node menu action."""
        data = action.data()
        if not data or not self._scene or not self._scene.network_model:
            return

        node_type, scene_pos = data

        from ...core.registry import NodeRegistry

        try:
            # Create node
            node = NodeRegistry.create_node(node_type)
            node.set_position(scene_pos.x(), scene_pos.y())

            # Add to network
            self._scene.network_model.add_node(node)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to create node: {e}")

    def frame_selection(self):
        """Frame the view on selected items or all items."""
        if not self._scene:
            return

        selected = self._scene.selectedItems()

        if selected:
            # Frame selected items
            rect = selected[0].sceneBoundingRect()
            for item in selected[1:]:
                rect = rect.united(item.sceneBoundingRect())
        else:
            # Frame all items
            rect = self._scene.itemsBoundingRect()

        if not rect.isEmpty():
            # Add padding
            rect.adjust(-50, -50, 50, 50)
            self.fitInView(rect, Qt.KeepAspectRatio)

            # Update zoom level
            self._zoom_level = self.transform().m11()

    def reset_zoom(self):
        """Reset zoom to 100%."""
        self.resetTransform()
        self._zoom_level = 1.0

    def zoom_in(self):
        """Zoom in."""
        if self._zoom_level < self.ZOOM_MAX:
            self._zoom_level *= self.ZOOM_STEP
            self.scale(self.ZOOM_STEP, self.ZOOM_STEP)

    def zoom_out(self):
        """Zoom out."""
        if self._zoom_level > self.ZOOM_MIN:
            self._zoom_level /= self.ZOOM_STEP
            self.scale(1.0 / self.ZOOM_STEP, 1.0 / self.ZOOM_STEP)
