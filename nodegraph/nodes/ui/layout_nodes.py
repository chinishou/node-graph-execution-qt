"""
Layout Nodes
============

Nodes for creating layout containers.
"""

from typing import Dict, Any
from PySide6.QtWidgets import QWidget, QVBoxLayout
from ..base import BaseNode


class VBoxLayoutNode(BaseNode):
    """
    VBox Layout Node - Creates a vertical box layout.

    Arranges child widgets vertically from top to bottom.
    Supports up to 5 child widgets.
    """

    category: str = "UI/Layouts"
    description: str = "Vertical box layout"

    def __init__(self, **kwargs):
        super().__init__(
            name="VBox Layout",
            node_type="VBoxLayoutNode",
            **kwargs
        )
        # Cache the widget to avoid recreating on each compute
        self._cached_widget = None
        self._cached_layout = None

    def setup(self) -> None:
        """Setup inputs, parameters, and outputs."""
        # Multiple optional inputs for child widgets
        for i in range(1, 6):
            self.add_input(f"child{i}", data_type="widget", label=f"Child {i}")

        # Layout parameters
        self.add_parameter("spacing", data_type="int", default_value=5, label="Spacing")
        self.add_parameter("margins", data_type="int", default_value=10, label="Margins")

        self.add_output("widget", data_type="widget", label="Container")

    def compute(self, **inputs) -> Dict[str, Any]:
        """Create or update the layout container."""
        # Create widget and layout if not cached
        if self._cached_widget is None:
            self._cached_widget = QWidget()
            self._cached_layout = QVBoxLayout(self._cached_widget)

        # Clear existing widgets from layout
        while self._cached_layout.count():
            item = self._cached_layout.takeAt(0)
            if item.widget():
                # Don't delete the widget, just remove from layout
                item.widget().setParent(None)

        # Update layout parameters
        spacing = self.parameter("spacing").value()
        margins = self.parameter("margins").value()

        self._cached_layout.setSpacing(spacing)
        self._cached_layout.setContentsMargins(margins, margins, margins, margins)

        # Add child widgets that are connected
        for i in range(1, 6):
            child = inputs.get(f"child{i}")
            if child and isinstance(child, QWidget):
                # Set parent to our container
                child.setParent(self._cached_widget)
                self._cached_layout.addWidget(child)

        # Add stretch at the end to push widgets to top
        self._cached_layout.addStretch()

        return {"widget": self._cached_widget}
