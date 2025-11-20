"""
Node Palette Widget
===================

Searchable node palette for creating nodes.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
    QTreeWidget, QTreeWidgetItem, QLabel, QFrame
)
from PySide6.QtCore import Qt, Signal, QPointF, QEvent
from PySide6.QtGui import QKeyEvent

from typing import TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from ...core.registry import NodeRegistry


class NodePaletteDialog(QWidget):
    """
    Searchable node palette with hierarchical menu.

    Shows categories on the left, search results on the right when typing.
    """

    node_selected = Signal(str, QPointF)  # node_type, position
    cancelled = Signal()

    def __init__(self, scene_pos: QPointF, parent=None):
        super().__init__(parent)

        self.scene_pos = scene_pos
        self.all_nodes: Dict[str, str] = {}  # {display_name: node_type}
        self.categories: Dict[str, List[tuple]] = {}  # {category: [(node_type, node_class)]}

        # Set window flags for popup behavior
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self._setup_ui()
        self._load_nodes()
        self._populate_categories()

        # Auto-focus search box
        self.search_box.setFocus()

    def _setup_ui(self):
        """Setup the UI."""
        self.setMinimumWidth(200)
        self.setMinimumHeight(300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Container with border
        container = QFrame()
        container.setObjectName("paletteContainer")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(4, 4, 4, 4)
        container_layout.setSpacing(4)

        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("node")
        self.search_box.textChanged.connect(self._on_search_changed)
        self.search_box.installEventFilter(self)
        container_layout.addWidget(self.search_box)

        # Content area (categories and results)
        self.content_layout = QHBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        container_layout.addLayout(self.content_layout)

        # Category tree (left side - always visible)
        self.category_tree = QTreeWidget()
        self.category_tree.setHeaderHidden(True)
        self.category_tree.setIndentation(12)
        self.category_tree.setMouseTracking(True)  # Enable hover tracking
        self.category_tree.itemClicked.connect(self._on_category_item_clicked)
        self.category_tree.itemEntered.connect(self._on_category_item_hovered)
        self.category_tree.installEventFilter(self)
        self.content_layout.addWidget(self.category_tree)

        # Results list (right side - only visible when searching)
        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self._on_result_item_clicked)
        self.results_list.installEventFilter(self)
        self.results_list.hide()  # Hidden by default
        self.content_layout.addWidget(self.results_list)

        layout.addWidget(container)

        # Style
        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                color: #dcdcdc;
            }
            QFrame#paletteContainer {
                background-color: #2d2d2d;
                border: 1px solid #1a1a1a;
            }
            QLineEdit {
                background-color: #3c3c3c;
                border: 1px solid #4c4c4c;
                border-radius: 2px;
                padding: 4px 6px;
                color: #dcdcdc;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #6c6c6c;
            }
            QTreeWidget {
                background-color: #2d2d2d;
                border: none;
                color: #dcdcdc;
                outline: none;
                font-size: 11px;
            }
            QTreeWidget::item {
                padding: 3px;
            }
            QTreeWidget::item:selected {
                background-color: #4a4a4a;
            }
            QTreeWidget::item:hover {
                background-color: #3a3a3a;
            }
            QListWidget {
                background-color: #2d2d2d;
                border-left: 1px solid #1a1a1a;
                color: #dcdcdc;
                outline: none;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 4px 8px;
            }
            QListWidget::item:selected {
                background-color: #4a4a4a;
            }
            QListWidget::item:hover {
                background-color: #3a3a3a;
            }
        """)

    def _load_nodes(self):
        """Load all available nodes from registry."""
        from ...core.registry import NodeRegistry

        categories = NodeRegistry.get_categories()

        for category in sorted(categories):
            nodes = NodeRegistry.get_nodes_by_category(category)
            self.categories[category] = sorted(nodes.items())

            for node_type, node_class in nodes.items():
                display_name = f"{node_type}"
                self.all_nodes[display_name] = node_type

    def _populate_categories(self):
        """Populate the category tree."""
        self.category_tree.clear()

        for category in sorted(self.categories.keys()):
            # Add category item
            category_item = QTreeWidgetItem(self.category_tree)
            category_item.setText(0, category)
            category_item.setData(0, Qt.UserRole, None)  # Categories don't create nodes

            # Add node items under category
            for node_type, node_class in self.categories[category]:
                node_item = QTreeWidgetItem(category_item)
                node_item.setText(0, node_type)
                node_item.setData(0, Qt.UserRole, node_type)

        # Adjust size based on content
        self._adjust_size()

    def _adjust_size(self):
        """Adjust widget size based on content."""
        # Calculate tree width based on content
        self.category_tree.resizeColumnToContents(0)
        tree_width = self.category_tree.sizeHintForColumn(0) + 40  # Add padding for scrollbar
        tree_width = max(180, min(tree_width, 400))  # Clamp between 180-400

        # Calculate tree height based on item count
        total_items = self.category_tree.topLevelItemCount()
        for i in range(total_items):
            item = self.category_tree.topLevelItem(i)
            total_items += item.childCount()

        tree_height = min(total_items * 22 + 40, 600)  # Max 600px height
        tree_height = max(200, tree_height)  # Min 200px

        # Set sizes
        self.category_tree.setMinimumWidth(tree_width)
        self.category_tree.setMaximumWidth(tree_width)

        # Adjust overall widget size
        total_width = tree_width + 8  # Add margins
        if self.results_list.isVisible():
            total_width += 200  # Add space for results list

        self.setFixedSize(total_width, tree_height)

    def _on_category_item_hovered(self, item: QTreeWidgetItem, column: int):
        """Handle category tree item hover - auto expand categories."""
        # Only expand if it's a category (has children)
        if item.childCount() > 0:
            # Expand the hovered category
            item.setExpanded(True)

    def _on_search_changed(self, text: str):
        """Handle search text change."""
        if text.strip():
            # Collapse all category tree items when showing search results
            self.category_tree.collapseAll()

            # Show search results
            self._show_search_results(text)
            self.results_list.show()
            if self.results_list.count() > 0:
                self.results_list.setCurrentRow(0)

            # Adjust size to include results panel
            self._adjust_size()
        else:
            # Hide search results
            self.results_list.hide()
            # Adjust size back to tree only
            self._adjust_size()

    def _show_search_results(self, filter_text: str):
        """Show filtered search results."""
        self.results_list.clear()

        # Filter using fuzzy matching
        results = self._fuzzy_filter(filter_text)

        # Add to results list
        for display_name, node_type in results:
            item = QListWidgetItem(display_name)
            item.setData(Qt.UserRole, node_type)
            self.results_list.addItem(item)

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

    def _on_category_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle category tree item click."""
        node_type = item.data(0, Qt.UserRole)
        if node_type:  # Node item, not category
            self._select_node(node_type)

    def _on_result_item_clicked(self, item: QListWidgetItem):
        """Handle result list item click."""
        node_type = item.data(Qt.UserRole)
        if node_type:
            self._select_node(node_type)

    def _select_node(self, node_type: str):
        """Select and emit node."""
        self.node_selected.emit(node_type, self.scene_pos)
        self.close()

    def eventFilter(self, obj, event):
        """Filter events for keyboard navigation."""
        if event.type() == QEvent.KeyPress:
            key = event.key()

            if key == Qt.Key_Escape:
                self.cancelled.emit()
                self.close()
                return True

            if key == Qt.Key_Return or key == Qt.Key_Enter:
                # Create selected node
                if self.results_list.isVisible():
                    current_item = self.results_list.currentItem()
                    if current_item:
                        node_type = current_item.data(Qt.UserRole)
                        self._select_node(node_type)
                        return True
                else:
                    current_item = self.category_tree.currentItem()
                    if current_item:
                        node_type = current_item.data(0, Qt.UserRole)
                        if node_type:
                            self._select_node(node_type)
                            return True
                return True

            if key in (Qt.Key_Up, Qt.Key_Down):
                # Navigate in the appropriate widget
                if self.results_list.isVisible():
                    if obj != self.results_list:
                        self.results_list.setFocus()
                        self.results_list.event(event)
                        self.search_box.setFocus()
                        return True
                else:
                    if obj != self.category_tree:
                        self.category_tree.setFocus()
                        self.category_tree.event(event)
                        self.search_box.setFocus()
                        return True

        return super().eventFilter(obj, event)
