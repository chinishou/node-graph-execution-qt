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

    def setup(self) -> None:
        """Setup parameters and outputs."""
        self.add_parameter("text", data_type="str", default_value="Label", label="Text")
        self.add_parameter("alignment", data_type="str", default_value="left",
                          label="Alignment", menu_items=["left", "center", "right"])
        self.add_output("widget", data_type="widget", label="Widget")

    def compute(self, **inputs) -> Dict[str, Any]:
        """Create the label widget."""
        # Create a fresh widget each time (simple and safe for manual refresh)
        label = QLabel()

        # Set properties
        text = self.parameter("text").value()
        alignment = self.parameter("alignment").value()

        label.setText(text)

        # Set alignment
        if alignment == "left":
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        elif alignment == "center":
            label.setAlignment(Qt.AlignCenter)
        elif alignment == "right":
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        return {"widget": label}
