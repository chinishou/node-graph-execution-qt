"""
Node Palette Widget
===================

Searchable node palette for creating nodes.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
    QLabel, QWidget, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QKeyEvent

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...core.registry import NodeRegistry


class NodePaletteDialog(QDialog):
    """
    Searchable node palette dialog.

    Shows all available nodes with fuzzy search/filtering.
    """

    node_selected = Signal(str, QPointF)  # node_type, position

    def __init__(self, scene_pos: QPointF, parent=None):
        super().__init__(parent)

        self.scene_pos = scene_pos
        self.all_nodes = {}  # {display_name: node_type}
        self.filtered_items = []

        self._setup_ui()
        self._load_nodes()
        self._update_list()

        # Auto-focus search box
        self.search_box.setFocus()

    def _setup_ui(self):
        """Setup the UI."""
        self.setWindowTitle("Add Node")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setMinimumHeight(500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Search box
        search_label = QLabel("Search:")
        layout.addWidget(search_label)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Type to filter nodes...")
        self.search_box.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_box)

        # Node list
        self.node_list = QListWidget()
        self.node_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.node_list)

        # Instructions
        info_label = QLabel("Double-click or press Enter to create node")
        info_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(info_label)

        # Style
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
                color: #dcdcdc;
            }
            QLineEdit {
                background-color: #3c3c3c;
                border: 1px solid #4c4c4c;
                border-radius: 3px;
                padding: 6px;
                color: #dcdcdc;
            }
            QLineEdit:focus {
                border: 1px solid #6c6c6c;
            }
            QListWidget {
                background-color: #2d2d2d;
                border: 1px solid #3c3c3c;
                color: #dcdcdc;
                outline: none;
            }
            QListWidget::item {
                padding: 6px;
                border-radius: 2px;
            }
            QListWidget::item:selected {
                background-color: #4a4a4a;
            }
            QListWidget::item:hover {
                background-color: #3a3a3a;
            }
            QLabel {
                color: #dcdcdc;
            }
        """)

    def _load_nodes(self):
        """Load all available nodes from registry."""
        from ...core.registry import NodeRegistry

        categories = NodeRegistry.get_categories()

        for category in sorted(categories):
            nodes = NodeRegistry.get_nodes_by_category(category)

            for node_type, node_class in sorted(nodes.items()):
                display_name = f"{category} > {node_type}"
                self.all_nodes[display_name] = node_type

    def _update_list(self, filter_text: str = ""):
        """Update the node list based on filter."""
        self.node_list.clear()
        self.filtered_items = []

        # Filter nodes
        if not filter_text:
            # Show all nodes grouped by category
            items = sorted(self.all_nodes.items())
        else:
            # Filter using fuzzy matching
            items = self._fuzzy_filter(filter_text)

        # Add to list
        for display_name, node_type in items:
            item = QListWidgetItem(display_name)
            item.setData(Qt.UserRole, node_type)
            self.node_list.addItem(item)
            self.filtered_items.append((display_name, node_type))

        # Auto-select first item
        if self.node_list.count() > 0:
            self.node_list.setCurrentRow(0)

    def _fuzzy_filter(self, filter_text: str):
        """
        Fuzzy filter nodes by text.

        Matches if all characters in filter_text appear in order in the node name.
        """
        filter_text = filter_text.lower()
        results = []

        for display_name, node_type in self.all_nodes.items():
            search_text = display_name.lower()

            # Simple fuzzy match: all filter chars must appear in order
            if self._fuzzy_match(filter_text, search_text):
                # Calculate match score (higher = better)
                score = self._match_score(filter_text, search_text)
                results.append((score, display_name, node_type))

        # Sort by score (best matches first)
        results.sort(reverse=True, key=lambda x: x[0])

        return [(name, typ) for _, name, typ in results]

    def _fuzzy_match(self, pattern: str, text: str) -> bool:
        """Check if pattern matches text (fuzzy)."""
        pattern_idx = 0

        for char in text:
            if pattern_idx < len(pattern) and char == pattern[pattern_idx]:
                pattern_idx += 1

        return pattern_idx == len(pattern)

    def _match_score(self, pattern: str, text: str) -> float:
        """Calculate match score (0-100)."""
        if not pattern:
            return 0

        # Exact match gets highest score
        if pattern == text:
            return 100

        # Starts with pattern gets high score
        if text.startswith(pattern):
            return 90

        # Contains pattern as substring gets medium score
        if pattern in text:
            return 80

        # Fuzzy match gets lower score
        return 50

    def _on_search_changed(self, text: str):
        """Handle search text change."""
        self._update_list(text)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        """Handle item double-click."""
        node_type = item.data(Qt.UserRole)
        self.node_selected.emit(node_type, self.scene_pos)
        self.accept()

    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press."""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Create selected node
            current_item = self.node_list.currentItem()
            if current_item:
                node_type = current_item.data(Qt.UserRole)
                self.node_selected.emit(node_type, self.scene_pos)
                self.accept()
            return

        if event.key() == Qt.Key_Escape:
            # Cancel
            self.reject()
            return

        if event.key() == Qt.Key_Up or event.key() == Qt.Key_Down:
            # Let list widget handle navigation
            self.node_list.setFocus()
            self.node_list.keyPressEvent(event)
            self.search_box.setFocus()
            return

        super().keyPressEvent(event)
