"""
Label Node
==========

Node for creating QLabel widgets.
"""

from typing import Dict, Any
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from ..base import BaseNode


class LabelNode(BaseNode):
    """
    Label Node - Creates a QLabel widget.

    Displays text in the UI preview.
    """

    category: str = "UI/Widgets"
    description: str = "Text label widget"

    def __init__(self, **kwargs):
        super().__init__(
            name="Label",
            node_type="LabelNode",
            **kwargs
        )
        # Cache the widget to avoid recreating on each compute
        self._cached_widget = None

    def setup(self) -> None:
        """Setup parameters and outputs."""
        self.add_parameter("text", data_type="str", default_value="Label", label="Text")
        self.add_parameter("alignment", data_type="str", default_value="left",
                          label="Alignment", menu_items=["left", "center", "right"])
        self.add_output("widget", data_type="widget", label="Widget")

    def compute(self, **inputs) -> Dict[str, Any]:
        """Create or update the label widget."""
        # Create widget if not cached
        if self._cached_widget is None:
            self._cached_widget = QLabel()

        # Update properties
        text = self.parameter("text").value()
        alignment = self.parameter("alignment").value()

        self._cached_widget.setText(text)

        # Set alignment
        if alignment == "left":
            self._cached_widget.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        elif alignment == "center":
            self._cached_widget.setAlignment(Qt.AlignCenter)
        elif alignment == "right":
            self._cached_widget.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        return {"widget": self._cached_widget}
