"""
Button Node
===========

Node for creating QPushButton widgets.
"""

from typing import Dict, Any
from PySide6.QtWidgets import QPushButton
from ..base import BaseNode


class ButtonNode(BaseNode):
    """
    Button Node - Creates a QPushButton widget.

    When clicked in preview, prints a message to console.
    """

    category: str = "UI/Widgets"
    description: str = "Push button widget"

    def __init__(self, **kwargs):
        super().__init__(
            name="Button",
            node_type="ButtonNode",
            **kwargs
        )

    def setup(self) -> None:
        """Setup parameters and outputs."""
        self.add_parameter("text", data_type="str", default_value="Button", label="Text")
        self.add_parameter("width", data_type="int", default_value=100, label="Min Width")
        self.add_parameter("height", data_type="int", default_value=30, label="Min Height")
        self.add_parameter("on_click_message", data_type="str",
                          default_value="Button clicked!", label="Click Message")
        self.add_output("widget", data_type="widget", label="Widget")

    def compute(self, **inputs) -> Dict[str, Any]:
        """Create the button widget."""
        # Create a fresh widget each time (simple and safe for manual refresh)
        button = QPushButton()

        # Set properties
        text = self.parameter("text").value()
        width = self.parameter("width").value()
        height = self.parameter("height").value()

        button.setText(text)
        button.setMinimumWidth(width)
        button.setMinimumHeight(height)

        # Connect click signal
        button.clicked.connect(self._on_button_clicked)

        return {"widget": button}

    def _on_button_clicked(self):
        """Handle button click in preview."""
        message = self.parameter("on_click_message").value()

        # Output to console
        print(f"[Preview] {self.name}: {message}")

        # Also output to the OutputPane if available
        try:
            from ...nodes.utils import print_output_signal
            print_output_signal.emit(self.name, message)
        except:
            pass  # OutputPane not available
