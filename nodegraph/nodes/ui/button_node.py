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
    Captures click events and exposes click_count as data output.
    """

    category: str = "UI/Widgets"
    description: str = "Push button widget"

    def __init__(self, **kwargs):
        super().__init__(
            name="Button",
            node_type="ButtonNode",
            **kwargs
        )
        # Signal data storage
        self._click_count = 0

    def setup(self) -> None:
        """Setup parameters and outputs."""
        self.add_parameter("text", data_type="str", default_value="Button", label="Text")
        self.add_parameter("width", data_type="int", default_value=100, label="Min Width")
        self.add_parameter("height", data_type="int", default_value=30, label="Min Height")
        self.add_parameter("on_click_message", data_type="str",
                          default_value="Button clicked!", label="Click Message")
        self.add_output("widget", data_type="widget", label="Widget")
        # Signal data outputs
        self.add_output("click_count", data_type="int", label="Click Count")

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

        # Return both widget and signal data
        return {
            "widget": button,
            "click_count": self._click_count
        }

    def _on_button_clicked(self):
        """Handle button click in preview."""
        # Update signal data
        self._click_count += 1

        message = self.parameter("on_click_message").value()

        # Output to console
        print(f"[Preview] {self.name}: {message} (Total clicks: {self._click_count})")

        # Also output to the OutputPane if available
        try:
            from ...nodes.utils import print_output_signal
            print_output_signal.emit(self.name, f"{message} (Total clicks: {self._click_count})")
        except:
            pass  # OutputPane not available
