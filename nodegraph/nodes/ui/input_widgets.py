"""
Input Widget Nodes
==================

Nodes for creating input widgets (LineEdit, ComboBox, etc).
"""

from typing import Dict, Any
from PySide6.QtWidgets import QLineEdit, QComboBox
from ..base import BaseNode


class LineEditNode(BaseNode):
    """
    LineEdit Node - Creates a QLineEdit widget.

    Single-line text input field.
    """

    category: str = "UI/Input"
    description: str = "Single-line text input"

    def __init__(self, **kwargs):
        super().__init__(
            name="LineEdit",
            node_type="LineEditNode",
            **kwargs
        )

    def setup(self) -> None:
        """Setup parameters and outputs."""
        self.add_parameter("text", data_type="str", default_value="", label="Default Text")
        self.add_parameter("placeholder", data_type="str", default_value="", label="Placeholder")
        self.add_parameter("width", data_type="int", default_value=200, label="Min Width")
        self.add_parameter("read_only", data_type="bool", default_value=False, label="Read Only")
        self.add_output("widget", data_type="widget", label="Widget")

    def compute(self, **inputs) -> Dict[str, Any]:
        """Create the line edit widget."""
        line_edit = QLineEdit()

        # Set properties
        text = self.parameter("text").value()
        placeholder = self.parameter("placeholder").value()
        width = self.parameter("width").value()
        read_only = self.parameter("read_only").value()

        if text:
            line_edit.setText(text)
        if placeholder:
            line_edit.setPlaceholderText(placeholder)

        line_edit.setMinimumWidth(width)
        line_edit.setReadOnly(read_only)

        # Connect signal to print changes
        line_edit.textChanged.connect(lambda t: self._on_text_changed(t))

        return {"widget": line_edit}

    def _on_text_changed(self, text: str):
        """Handle text change in preview."""
        print(f"[Preview] {self.name}: Text changed to '{text}'")

        # Also output to OutputPane if available
        try:
            from ...nodes.utils import print_output_signal
            print_output_signal.emit(self.name, f"Text: {text}")
        except:
            pass


class ComboBoxNode(BaseNode):
    """
    ComboBox Node - Creates a QComboBox widget.

    Dropdown selection widget with customizable items.
    """

    category: str = "UI/Input"
    description: str = "Dropdown selection box"

    def __init__(self, **kwargs):
        super().__init__(
            name="ComboBox",
            node_type="ComboBoxNode",
            **kwargs
        )

    def setup(self) -> None:
        """Setup parameters and outputs."""
        self.add_parameter("items", data_type="str",
                          default_value="Option 1,Option 2,Option 3",
                          label="Items (comma-separated)")
        self.add_parameter("current_index", data_type="int", default_value=0,
                          label="Default Index")
        self.add_parameter("width", data_type="int", default_value=150, label="Min Width")
        self.add_output("widget", data_type="widget", label="Widget")

    def compute(self, **inputs) -> Dict[str, Any]:
        """Create the combo box widget."""
        combo_box = QComboBox()

        # Parse items from comma-separated string
        items_str = self.parameter("items").value()
        items = [item.strip() for item in items_str.split(",") if item.strip()]

        # Add items to combo box
        combo_box.addItems(items)

        # Set current index
        current_index = self.parameter("current_index").value()
        if 0 <= current_index < len(items):
            combo_box.setCurrentIndex(current_index)

        # Set width
        width = self.parameter("width").value()
        combo_box.setMinimumWidth(width)

        # Connect signal
        combo_box.currentIndexChanged.connect(lambda idx: self._on_selection_changed(idx))

        return {"widget": combo_box}

    def _on_selection_changed(self, index: int):
        """Handle selection change in preview."""
        # Get the combo box from sender (if available)
        sender = None
        try:
            from PySide6.QtCore import QObject
            # In a real scenario, we'd need to store reference to connect properly
            # For now, just print the index
            print(f"[Preview] {self.name}: Selected index {index}")
        except:
            pass

        # Output to OutputPane if available
        try:
            from ...nodes.utils import print_output_signal
            print_output_signal.emit(self.name, f"Selected: Index {index}")
        except:
            pass
