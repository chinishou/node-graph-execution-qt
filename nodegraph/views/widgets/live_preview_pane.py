"""
Live Preview Pane
=================

Preview pane for displaying UI built from node graph.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ...core.models import NetworkModel


class LivePreviewPane(QWidget):
    """
    Live preview pane for UI widgets.

    Displays UI constructed from node graph with UIRootNode as entry point.
    Uses manual refresh mode - user clicks "Refresh" button to rebuild UI.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self._network_model: Optional["NetworkModel"] = None
        self._preview_widget: Optional[QWidget] = None

        self._setup_ui()

    def _setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Title bar with refresh button
        title_bar = QHBoxLayout()

        title_label = QLabel("Live Preview")
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_bar.addWidget(title_label)

        title_bar.addStretch()

        # Refresh button
        self._refresh_button = QPushButton("🔄 Refresh")
        self._refresh_button.setToolTip("Rebuild UI from node graph")
        self._refresh_button.clicked.connect(self.refresh_preview)
        title_bar.addWidget(self._refresh_button)

        layout.addLayout(title_bar)

        # Scroll area for preview content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.StyledPanel)

        # Container for preview widget
        self._preview_container = QWidget()
        self._preview_layout = QVBoxLayout(self._preview_container)
        self._preview_layout.setContentsMargins(10, 10, 10, 10)
        self._preview_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        scroll_area.setWidget(self._preview_container)
        layout.addWidget(scroll_area)

        # Initial placeholder
        self._show_placeholder("No UIRootNode found.\n\nCreate a UIRootNode and connect UI widgets to preview.")

        # Style
        self.setStyleSheet("""
            LivePreviewPane {
                background-color: #2d2d2d;
            }
            QLabel {
                color: #dcdcdc;
            }
            QPushButton {
                background-color: #4c4c4c;
                color: #dcdcdc;
                border: 1px solid #5c5c5c;
                border-radius: 3px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #5c5c5c;
            }
            QPushButton:pressed {
                background-color: #3c3c3c;
            }
            QScrollArea {
                background-color: #3c3c3c;
                border: 1px solid #5c5c5c;
            }
            QWidget#preview_container {
                background-color: #3c3c3c;
            }
        """)

    def set_network(self, network: "NetworkModel"):
        """Set the network to preview."""
        self._network_model = network
        # Note: We don't auto-refresh here, user must click Refresh button

    def refresh_preview(self):
        """Rebuild and display UI from node graph."""
        if not self._network_model:
            self._show_placeholder("No network set.")
            return

        # Find UIRootNode
        root_node = self._find_ui_root_node()
        if not root_node:
            self._show_placeholder("No UIRootNode found.\n\nCreate a UIRootNode and connect UI widgets to preview.")
            return

        try:
            # Execute the root node to get the widget
            success = root_node.execute()

            if not success:
                self._show_placeholder("Failed to execute UIRootNode.\n\nCheck node connections and parameters.")
                return

            # Get the widget output
            widget = root_node.get_output_value("widget")

            if widget is None:
                self._show_placeholder("UIRootNode returned None.\n\nConnect a UI widget to the UIRootNode input.")
                return

            if not isinstance(widget, QWidget):
                self._show_placeholder(f"UIRootNode output is not a QWidget.\n\nGot: {type(widget).__name__}")
                return

            # Successfully got a widget - display it
            self._set_preview_widget(widget)

        except Exception as e:
            self._show_placeholder(f"Error building UI:\n\n{str(e)}")
            import traceback
            traceback.print_exc()

    def _find_ui_root_node(self):
        """Find UIRootNode in the current network."""
        if not self._network_model:
            return None

        for node in self._network_model.nodes():
            if node.node_type == "UIRootNode":
                return node

        return None

    def _set_preview_widget(self, widget: QWidget):
        """Display a widget in the preview pane."""
        # Clear old widget
        self._clear_preview()

        # Set new widget
        self._preview_widget = widget
        self._preview_layout.addWidget(widget)
        self._preview_layout.addStretch()

    def _show_placeholder(self, message: str):
        """Show a placeholder message."""
        self._clear_preview()

        label = QLabel(message)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 12px;
                padding: 20px;
            }
        """)

        self._preview_layout.addStretch()
        self._preview_layout.addWidget(label)
        self._preview_layout.addStretch()

    def _clear_preview(self):
        """Clear the preview area."""
        # Remove all widgets from layout
        while self._preview_layout.count():
            item = self._preview_layout.takeAt(0)
            if item.widget():
                widget = item.widget()
                widget.setParent(None)
                widget.deleteLater()

        self._preview_widget = None
