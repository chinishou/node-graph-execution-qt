"""
Label Node
==========

Node for creating QLabel widgets with click support.
"""

from typing import Dict, Any
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, Signal
from ..base import BaseNode


class ClickableLabel(QLabel):
    """QLabel subclass that emits a clicked signal when clicked."""
    clicked = Signal()

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class LabelNode(BaseNode):
    """
    Label Node - Creates a clickable QLabel widget.

    Displays text in the UI preview with push-based trigger support.
    When clicked in preview, triggers execution of all connected nodes.
    """

    category: str = "UI/Widgets"
    description: str = "Clickable text label widget"

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
        self.add_parameter("on_click_message", data_type="str",
                          default_value="Label clicked!", label="Click Message")
        self.add_output("widget", data_type="widget", label="Widget")
        # Signal trigger output - executes connected nodes when clicked
        self.add_output("clicked", data_type="any", label="Clicked")

    def compute(self, **inputs) -> Dict[str, Any]:
        """Create the label widget."""
        # Create a fresh clickable widget each time
        label = ClickableLabel()

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

        # Connect click signal to trigger downstream nodes
        label.clicked.connect(self._on_label_clicked)

        # Return both widget and None for clicked (no click yet)
        return {
            "widget": label,
            "clicked": None
        }

    def _on_label_clicked(self):
        """Handle label click in preview - triggers connected nodes."""
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
        self._trigger_connected_nodes(True)

    def _trigger_connected_nodes(self, signal_value):
        """
        Execute all nodes connected to the 'clicked' output.

        Args:
            signal_value: Value from the click event (True for clicked)
        """
        # Get the 'clicked' output connector
        clicked_output = self.output("clicked")
        if not clicked_output:
            return

        # Get all connections from this output
        connections = clicked_output.connections()
        if not connections:
            return

        print(f"[Trigger] Label '{self.name}' clicked, executing {len(connections)} connected node(s)...")

        # Store the signal value temporarily for connected nodes to read
        self._last_outputs["clicked"] = signal_value

        # Execute each connected node
        for conn in connections:
            if conn.node:
                try:
                    print(f"[Trigger] Executing {conn.node.name}...")
                    conn.node.execute()
                except Exception as e:
                    print(f"[Trigger] Error executing {conn.node.name}: {e}")
