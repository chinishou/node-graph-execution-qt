"""
Node Palette Widget
===================

Searchable node palette for creating nodes.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
    QLabel, QFrame
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
        self._create_category_menu()

        # Auto-focus search box
        self.search_box.setFocus()

    def _setup_ui(self):
        """Setup the UI."""
        self.setMinimumWidth(200)
        self.setMinimumHeight(100)

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

        # Content area (categories menu and search results)
        self.content_layout = QHBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        container_layout.addLayout(self.content_layout)

        # Category list (left side - shows category names, hover to show submenu)
        self.category_list = QListWidget()
        self.category_list.setMouseTracking(True)
        self.category_list.itemEntered.connect(self._on_category_hovered)
        self.category_list.itemClicked.connect(self._on_category_clicked)
        self.category_list.installEventFilter(self)
        self.content_layout.addWidget(self.category_list)

        # Right side list (for both node list and search results)
        self.right_list = QListWidget()
        self.right_list.itemClicked.connect(self._on_right_item_clicked)
        self.right_list.installEventFilter(self)
        self.right_list.hide()  # Hidden by default
        self.content_layout.addWidget(self.right_list)

        # Track current mode: 'category' or 'search'
        self.right_list_mode = None

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
            QListWidget {
                background-color: #2d2d2d;
                border: none;
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
            QMenu {
                background-color: #2d2d2d;
                border: 1px solid #1a1a1a;
                color: #dcdcdc;
                font-size: 11px;
            }
            QMenu::item {
                padding: 4px 20px 4px 8px;
            }
            QMenu::item:selected {
                background-color: #4a4a4a;
            }
            QMenu::item:hover {
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

    def _create_category_menu(self):
        """Create hierarchical menu structure for categories."""
        # Populate category list
        self.category_list.clear()

        for category in sorted(self.categories.keys()):
            item = QListWidgetItem(category)
            item.setData(Qt.UserRole, category)
            self.category_list.addItem(item)

        # Adjust size based on content
        self._adjust_size()

    def _adjust_size(self):
        """Adjust widget size based on content."""
        # Calculate list width based on content
        max_width = 180
        for i in range(self.category_list.count()):
            item = self.category_list.item(i)
            text_width = self.category_list.fontMetrics().horizontalAdvance(item.text())
            max_width = max(max_width, text_width + 30)

        list_width = min(max_width, 400)  # Clamp to max 400px

        # Calculate height based on item count
        item_count = self.category_list.count()
        list_height = min(item_count * 24 + 8, 400)  # Max 400px height
        list_height = max(100, list_height)  # Min 100px

        # Set sizes
        self.category_list.setFixedWidth(list_width)
        self.category_list.setFixedHeight(list_height)

        # Adjust overall widget size
        total_width = list_width + 8  # Add margins
        total_height = list_height + 40  # Add search box height + margins

        if self.right_list.isVisible():
            # Calculate right list width based on content
            right_width = 200
            for i in range(self.right_list.count()):
                item = self.right_list.item(i)
                text_width = self.right_list.fontMetrics().horizontalAdvance(item.text())
                right_width = max(right_width, text_width + 30)
            right_width = min(right_width, 400)

            total_width += right_width  # Add space for right list
            self.right_list.setFixedWidth(right_width)
            self.right_list.setFixedHeight(list_height)

        self.setFixedSize(total_width, total_height)

    def _on_category_hovered(self, item: QListWidgetItem):
        """Handle category hover - show node list."""
        # Don't show node list when in search mode
        if self.right_list_mode == 'search':
            return

        category = item.data(Qt.UserRole)
        if not category or category not in self.categories:
            return

        # Populate right list with nodes from this category
        self.right_list.clear()
        self.right_list_mode = 'category'

        for node_type, node_class in self.categories[category]:
            list_item = QListWidgetItem(node_type)
            list_item.setData(Qt.UserRole, node_type)
            self.right_list.addItem(list_item)

        # Show right list and adjust size
        self.right_list.show()
        self._adjust_size()

    def _on_category_clicked(self, item: QListWidgetItem):
        """Handle category click - same as hover."""
        self._on_category_hovered(item)

    def _on_search_changed(self, text: str):
        """Handle search text change."""
        if text.strip():
            # Show search results
            self.right_list_mode = 'search'
            self._show_search_results(text)
            self.right_list.show()
            if self.right_list.count() > 0:
                self.right_list.setCurrentRow(0)

            # Adjust size to include results panel
            self._adjust_size()
        else:
            # Hide right list
            self.right_list_mode = None
            self.right_list.hide()
            # Adjust size back to category list only
            self._adjust_size()

    def _show_search_results(self, filter_text: str):
        """Show filtered search results."""
        self.right_list.clear()

        # Filter using fuzzy matching
        results = self._fuzzy_filter(filter_text)

        # Add to right list
        for display_name, node_type in results:
            item = QListWidgetItem(display_name)
            item.setData(Qt.UserRole, node_type)
            self.right_list.addItem(item)

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

    def _on_right_item_clicked(self, item: QListWidgetItem):
        """Handle right list item click (both search results and category nodes)."""
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
                if self.right_list.isVisible():
                    current_item = self.right_list.currentItem()
                    if current_item:
                        node_type = current_item.data(Qt.UserRole)
                        self._select_node(node_type)
                        return True
                else:
                    # Trigger hover on selected category item
                    current_item = self.category_list.currentItem()
                    if current_item:
                        self._on_category_hovered(current_item)
                        return True
                return True

            if key in (Qt.Key_Up, Qt.Key_Down):
                # Navigate in the appropriate widget
                if self.right_list.isVisible():
                    # When right list is visible (both search and category mode)
                    if self.right_list_mode == 'search':
                        # In search mode, keep focus on search box
                        if obj != self.right_list:
                            self.right_list.setFocus()
                            self.right_list.event(event)
                            self.search_box.setFocus()
                            return True
                    else:
                        # In category mode, navigate right list directly
                        self.right_list.setFocus()
                        self.right_list.event(event)
                        return True
                else:
                    # No right list, navigate category list
                    if obj != self.category_list:
                        self.category_list.setFocus()
                        self.category_list.event(event)
                        self.search_box.setFocus()
                        return True

            if key in (Qt.Key_Right, Qt.Key_Left):
                # Right arrow opens node list, left arrow closes it
                if self.right_list_mode != 'search':
                    if key == Qt.Key_Right:
                        if self.right_list.isVisible():
                            # Focus on right list
                            self.right_list.setFocus()
                            if self.right_list.count() > 0:
                                self.right_list.setCurrentRow(0)
                            return True
                        else:
                            # Open node list for current category
                            current_item = self.category_list.currentItem()
                            if current_item:
                                self._on_category_hovered(current_item)
                                # After opening, focus on right list
                                self.right_list.setFocus()
                                if self.right_list.count() > 0:
                                    self.right_list.setCurrentRow(0)
                                return True
                    elif key == Qt.Key_Left:
                        if self.right_list.isVisible():
                            # Close right list and return to category list
                            self.right_list.hide()
                            self.right_list_mode = None
                            self.category_list.setFocus()
                            self._adjust_size()
                            return True

        return super().eventFilter(obj, event)
