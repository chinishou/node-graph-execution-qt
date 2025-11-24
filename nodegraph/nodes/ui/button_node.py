"""
Button Node
===========

Node for creating QPushButton widgets with signal trigger support.
"""

from typing import Dict, Any
from PySide6.QtWidgets import QPushButton
from ..base import BaseNode


class ButtonNode(BaseNode):
    """
    Button Node - Creates a QPushButton widget.

    When clicked in preview, triggers execution of all connected nodes.
    The 'clicked' output propagates the click event to downstream nodes.
    """

    category: str = "UI/Widgets"
    description: str = "Push button widget with click trigger"

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
        # Signal trigger output - executes connected nodes when clicked
        self.add_output("clicked", data_type="any", label="Clicked")

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

        # Connect click signal to trigger downstream nodes
        button.clicked.connect(self._on_button_clicked)

        # Return both widget and None for clicked (no click yet)
        return {
            "widget": button,
            "clicked": None
        }

    def _on_button_clicked(self, checked=False):
        """Handle button click in preview - triggers connected nodes."""
        message = self.parameter("on_click_message").value()

        # Output to console
        print(f"[Preview] {self.name}: {message}")

        # Also output to the OutputPane if available
        try:
            from ...nodes.utils import print_output_signal
            print_output_signal.emit(self.name, message)
        except:
            pass  # OutputPane not available

        # Trigger execution of all connected nodes
        self._trigger_connected_nodes(checked)

    def _trigger_connected_nodes(self, signal_value):
        """
        Execute all nodes connected to the 'clicked' output.

        Args:
            signal_value: Value from the Qt signal (bool for clicked)
        """
        # Get the 'clicked' output connector
        clicked_output = self.output("clicked")
        if not clicked_output:
            return

        # Get all connections from this output
        connections = clicked_output.connections()
        if not connections:
            return

        print(f"[Trigger] Button '{self.name}' clicked, executing {len(connections)} connected node(s)...")

        # Store the signal value temporarily for connected nodes to read
        self._output_values["clicked"] = signal_value

        # Execute each connected node
        for conn in connections:
            if conn.node:
                try:
                    print(f"[Trigger] Executing {conn.node.name}...")
                    conn.node.execute()
                except Exception as e:
                    print(f"[Trigger] Error executing {conn.node.name}: {e}")
