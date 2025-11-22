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
        self._click_to_connect_port: Optional["PortGraphicsItem"] = None  # For click-click connection
        self._press_pos = QPointF()  # Track initial press position
        self._drag_threshold = 5  # Pixels to move before considering it a drag
        self._copied_nodes = []  # Store copied node data for paste
        self._navigation_controller = None  # Will be set by MainWindow

        # Setup view
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.RubberBandDrag)

        # Set large scene rect for unlimited panning
        self.setSceneRect(-10000, -10000, 20000, 20000)

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
                # Check if we're in click-to-connect mode
                if self._click_to_connect_port is not None:
                    # Second click: complete the connection
                    self._complete_click_connection(port)
                    event.accept()
                    return
                else:
                    # First click on port: prepare for both drag and click modes
                    self._click_to_connect_port = port
                    self._press_pos = event.position()
                    self._scene.start_connection_drag(port)
                    # Don't set _connecting yet - wait for mouse movement
                    event.accept()
                    return
            else:
                # Clicked on empty space: cancel click-to-connect mode
                if self._click_to_connect_port is not None:
                    self._cancel_click_connection()

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

        # Handle connection dragging or click-to-connect mode
        if self._click_to_connect_port and self._scene:
            # Check if we should enter drag mode (moved beyond threshold)
            if not self._connecting:
                delta = event.position() - self._press_pos
                distance = (delta.x() ** 2 + delta.y() ** 2) ** 0.5
                if distance > self._drag_threshold:
                    # Enter drag mode
                    self._connecting = True

            # Update temporary connection line (in both drag and click modes)
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

        if event.button() == Qt.LeftButton:
            if self._connecting:
                # Finish drag connection mode
                scene_pos = self.mapToScene(event.position().toPoint())
                if self._scene:
                    success = self._scene.finish_connection_drag(scene_pos)
                    if success:
                        # Connection completed, clean up
                        self._click_to_connect_port = None
                        self._connecting = False
                    else:
                        # Connection failed, stay in click-to-connect mode
                        self._connecting = False
                        # Keep _click_to_connect_port for second click
                event.accept()
                return
            elif self._click_to_connect_port:
                # Mouse released without dragging - stay in click-to-connect mode
                # The temporary line will continue following the cursor
                event.accept()
                return

        super().mouseReleaseEvent(event)

    def event(self, event):
        """Override event to catch Tab key before focus system."""
        if event.type() == event.Type.KeyPress:
            key_event = event
            if key_event.key() == Qt.Key_Tab:
                # Show node palette at cursor position
                cursor_pos = self.mapFromGlobal(self.cursor().pos())
                scene_pos = self.mapToScene(cursor_pos)
                self._show_node_menu(self.mapToGlobal(cursor_pos), scene_pos)
                return True
        return super().event(event)

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

        if event.key() == Qt.Key_U:
            # Go up one level (back to parent network)
            if hasattr(self, '_navigation_controller') and self._navigation_controller:
                self._navigation_controller.go_up()
            event.accept()
            return

        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Enter selected subnet
            self._enter_selected_subnet()
            event.accept()
            return

        # Copy selected nodes (Ctrl+C)
        if event.key() == Qt.Key_C and event.modifiers() & Qt.ControlModifier:
            self._copy_selected_nodes()
            event.accept()
            return

        # Paste nodes (Ctrl+V)
        if event.key() == Qt.Key_V and event.modifiers() & Qt.ControlModifier:
            self._paste_nodes()
            event.accept()
            return

        super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        """Show context menu on right-click."""
        scene_pos = self.mapToScene(event.pos())

        # Check if clicking on empty space
        item = self.itemAt(event.pos())
        if item is None:
            self._show_context_menu(event.globalPos(), scene_pos)
        else:
            # Show item-specific menu
            super().contextMenuEvent(event)

    def _show_context_menu(self, global_pos, scene_pos: QPointF):
        """Show context menu for empty space."""
        menu = QMenu(self)

        # Add sticky note options
        sticky_note_menu = menu.addMenu("Add Sticky Note")

        # Color options
        colors = {
            'Yellow': 'yellow',
            'Green': 'green',
            'Blue': 'blue',
            'Pink': 'pink',
            'Orange': 'orange',
            'Purple': 'purple',
        }

        for color_name, color_key in colors.items():
            action = sticky_note_menu.addAction(color_name)
            action.triggered.connect(lambda checked=False, c=color_key, p=scene_pos:
                                   self._create_sticky_note(p, c))

        menu.addSeparator()

        # Add nodes option
        add_node_action = menu.addAction("Add Node...")
        add_node_action.triggered.connect(lambda: self._show_node_menu(global_pos, scene_pos))

        menu.exec(global_pos)

    def _create_sticky_note(self, scene_pos: QPointF, color: str = 'yellow'):
        """Create a sticky note at the given position."""
        if self._scene:
            note = self._scene.add_sticky_note(position=scene_pos, color=color)
            # Optionally select and focus the note for immediate editing
            self._scene.clearSelection()
            note.setSelected(True)

    def _show_node_menu(self, global_pos, scene_pos: QPointF):
        """Show the node creation menu with search."""
        from ..widgets.node_palette import NodePaletteDialog

        # Determine if we're inside a subnet
        is_inside_subnet = False
        if hasattr(self, '_navigation_controller') and self._navigation_controller:
            # Check if we're at depth > 0 (inside a subnet)
            location = self._navigation_controller.get_current_location()
            if location and len(location.path) > 0:
                is_inside_subnet = True

        # Create and show searchable node palette as popup
        palette = NodePaletteDialog(scene_pos, self, is_inside_subnet=is_inside_subnet)
        palette.node_selected.connect(self._on_node_palette_selected)
        palette.cancelled.connect(lambda: palette.close())

        # Position the popup near the cursor
        palette.move(global_pos)
        palette.show()

    def _on_node_palette_selected(self, node_type: str, scene_pos: QPointF):
        """Handle node selection from palette."""
        if not self._scene or not self._scene.network_model:
            return

        from ...core.registry import NodeRegistry

        try:
            # Create node
            node = NodeRegistry.create_node(node_type)
            node.set_position(scene_pos.x(), scene_pos.y())

            # Add to network
            self._scene.network_model.add_node(node)

            # If in click-to-connect mode, auto-connect to first available input
            if self._click_to_connect_port is not None:
                # Find the node graphics item for the newly created node
                node_item = self._scene.get_node_item(node.id)
                if node_item:
                    # Find first input port that can be connected
                    source_port = self._click_to_connect_port
                    for input_name, input_connector in node.inputs().items():
                        target_port = node_item.get_port(input_name, is_output=False)
                        if target_port:
                            # Try to connect
                            if source_port.is_output:
                                # Source is output, target is input
                                success = self._scene.create_connection(source_port, target_port)
                                if success:
                                    # Connection succeeded, clean up click-to-connect mode
                                    self._cancel_click_connection()
                                    break
                            elif not source_port.is_output:
                                # Source is input, need to connect from new node's first output
                                for output_name, output_connector in node.outputs().items():
                                    output_port = node_item.get_port(output_name, is_output=True)
                                    if output_port:
                                        success = self._scene.create_connection(output_port, source_port)
                                        if success:
                                            self._cancel_click_connection()
                                            break
                                    break

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to create node: {e}")

    def _complete_click_connection(self, target_port: "PortGraphicsItem"):
        """Complete a click-to-connect connection."""
        if not self._click_to_connect_port or not self._scene:
            return

        source_port = self._click_to_connect_port

        # Validate connection
        if source_port.is_output == target_port.is_output:
            # Can't connect input to input or output to output
            self._cancel_click_connection()
            return

        if source_port.connector.node == target_port.connector.node:
            # Can't connect to same node
            self._cancel_click_connection()
            return

        # Determine which is source and which is target
        if source_port.is_output:
            output_port = source_port
            input_port = target_port
        else:
            output_port = target_port
            input_port = source_port

        # Create the connection
        self._scene.create_connection(output_port, input_port)

        # Clean up
        self._cancel_click_connection()

    def _cancel_click_connection(self):
        """Cancel click-to-connect mode."""
        if self._click_to_connect_port and self._scene:
            # Remove temporary connection if it exists
            self._scene.cancel_connection_drag()

        self._click_to_connect_port = None
        self._connecting = False

    def _on_node_menu_action(self, action):
        """Handle node menu action (legacy, for compatibility)."""
        data = action.data()
        if not data or not self._scene or not self._scene.network_model:
            return

        node_type, scene_pos = data
        self._on_node_palette_selected(node_type, scene_pos)

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

    def _copy_selected_nodes(self):
        """Copy selected nodes to clipboard."""
        if not self._scene:
            return

        from ..nodes.node_graphics_item import NodeGraphicsItem

        selected = self._scene.selectedItems()
        self._copied_nodes = []

        for item in selected:
            if isinstance(item, NodeGraphicsItem):
                node = item.node_model
                # Get position using position() method
                pos = node.position()
                # Serialize node data
                node_data = {
                    'node_type': node.node_type,
                    'position': pos,  # Use tuple from position() method
                    'parameters': {}
                }

                # Copy parameter values
                for name, param in node.parameters().items():
                    node_data['parameters'][name] = param.value()

                # Copy input default values
                node_data['input_defaults'] = {}
                for name, connector in node.inputs().items():
                    node_data['input_defaults'][name] = connector.default_value

                self._copied_nodes.append(node_data)

        if self._copied_nodes:
            print(f"Copied {len(self._copied_nodes)} node(s)")

    def _paste_nodes(self):
        """Paste copied nodes."""
        if not self._scene or not self._scene.network_model or not self._copied_nodes:
            return

        from ...core.registry import NodeRegistry

        # Get cursor position in scene coords
        cursor_pos = self.mapFromGlobal(self.cursor().pos())
        scene_pos = self.mapToScene(cursor_pos)

        # Calculate offset for pasting
        if self._copied_nodes:
            # Calculate center of copied nodes
            min_x = min(data['position'][0] for data in self._copied_nodes)
            min_y = min(data['position'][1] for data in self._copied_nodes)

            offset_x = scene_pos.x() - min_x
            offset_y = scene_pos.y() - min_y

            new_nodes = []
            for node_data in self._copied_nodes:
                try:
                    # Create new node
                    node = NodeRegistry.create_node(node_data['node_type'])

                    # Set position with offset
                    orig_x, orig_y = node_data['position']
                    node.set_position(orig_x + offset_x, orig_y + offset_y)

                    # Restore parameter values
                    for name, value in node_data.get('parameters', {}).items():
                        param = node.parameter(name)
                        if param:
                            param.set_value(value)

                    # Restore input default values
                    for name, value in node_data.get('input_defaults', {}).items():
                        connector = node.input(name)
                        if connector:
                            connector.default_value = value

                    # Add to network
                    self._scene.network_model.add_node(node)
                    new_nodes.append(node)

                except Exception as e:
                    print(f"Error pasting node: {e}")

            # Select newly pasted nodes
            if new_nodes:
                self._scene.clearSelection()
                for node in new_nodes:
                    node_item = self._scene.get_node_item(node.id)
                    if node_item:
                        node_item.setSelected(True)

            print(f"Pasted {len(new_nodes)} node(s)")

    def set_navigation_controller(self, controller):
        """Set the navigation controller."""
        self._navigation_controller = controller

    def _enter_selected_subnet(self):
        """Enter the selected subnet node (if any)."""
        if not self._scene or not self._navigation_controller:
            return

        from ..nodes.node_graphics_item import NodeGraphicsItem
        from ...nodes.subnet import SubnetNode

        # Get selected items
        selected = self._scene.selectedItems()

        # Find first selected subnet node
        for item in selected:
            if isinstance(item, NodeGraphicsItem):
                node = item.node_model
                if isinstance(node, SubnetNode):
                    # Navigate into this subnet
                    self._navigation_controller.navigate_to_subnet(node)
                    return

    def mouseDoubleClickEvent(self, event):
        """Handle double-click to enter subnet."""
        # Check if double-clicking on a node
        item = self.itemAt(event.pos())

        if item:
            from ..nodes.node_graphics_item import NodeGraphicsItem
            from ...nodes.subnet import SubnetNode

            # Find the node item
            while item and not isinstance(item, NodeGraphicsItem):
                item = item.parentItem()

            if isinstance(item, NodeGraphicsItem):
                node = item.node_model
                if isinstance(node, SubnetNode):
                    # Enter the subnet
                    if self._navigation_controller:
                        self._navigation_controller.navigate_to_subnet(node)
                    event.accept()
                    return

        super().mouseDoubleClickEvent(event)
