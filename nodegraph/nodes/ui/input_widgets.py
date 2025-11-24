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
    Captures text changes and exposes current_text as data output.
    """

    category: str = "UI/Input"
    description: str = "Single-line text input"

    def __init__(self, **kwargs):
        super().__init__(
            name="LineEdit",
            node_type="LineEditNode",
            **kwargs
        )
        # Signal data storage
        self._current_text = ""

    def setup(self) -> None:
        """Setup parameters and outputs."""
        self.add_parameter("text", data_type="str", default_value="", label="Default Text")
        self.add_parameter("placeholder", data_type="str", default_value="", label="Placeholder")
        self.add_parameter("width", data_type="int", default_value=200, label="Min Width")
        self.add_parameter("read_only", data_type="bool", default_value=False, label="Read Only")
        self.add_output("widget", data_type="widget", label="Widget")
        # Signal data outputs
        self.add_output("current_text", data_type="str", label="Current Text")

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
            # Initialize current_text with default text
            self._current_text = text
        if placeholder:
            line_edit.setPlaceholderText(placeholder)

        line_edit.setMinimumWidth(width)
        line_edit.setReadOnly(read_only)

        # Connect signal to capture text changes
        line_edit.textChanged.connect(lambda t: self._on_text_changed(t))

        # Return both widget and signal data
        return {
            "widget": line_edit,
            "current_text": self._current_text
        }

    def _on_text_changed(self, text: str):
        """Handle text change in preview."""
        # Update signal data
        self._current_text = text

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
    Captures selection changes and exposes selected_index and selected_text as data outputs.
    """

    category: str = "UI/Input"
    description: str = "Dropdown selection box"

    def __init__(self, **kwargs):
        super().__init__(
            name="ComboBox",
            node_type="ComboBoxNode",
            **kwargs
        )
        # Signal data storage (-1 indicates not initialized)
        self._selected_index = -1
        self._selected_text = ""

    def setup(self) -> None:
        """Setup parameters and outputs."""
        self.add_parameter("items", data_type="str",
                          default_value="Option 1,Option 2,Option 3",
                          label="Items (comma-separated)")
        self.add_parameter("current_index", data_type="int", default_value=0,
                          label="Default Index")
        self.add_parameter("width", data_type="int", default_value=150, label="Min Width")
        self.add_output("widget", data_type="widget", label="Widget")
        # Signal data outputs
        self.add_output("selected_index", data_type="int", label="Selected Index")
        self.add_output("selected_text", data_type="str", label="Selected Text")

    def compute(self, **inputs) -> Dict[str, Any]:
        """Create the combo box widget."""
        combo_box = QComboBox()

        # Parse items from comma-separated string
        items_str = self.parameter("items").value()
        items = [item.strip() for item in items_str.split(",") if item.strip()]

        # Add items to combo box
        combo_box.addItems(items)

        # Initialize selection data on first execution
        if self._selected_index == -1:
            current_index = self.parameter("current_index").value()
            if 0 <= current_index < len(items):
                self._selected_index = current_index
                self._selected_text = items[current_index] if items else ""
            else:
                self._selected_index = 0
                self._selected_text = items[0] if items else ""

        # Set widget to match stored selection (from user interaction or default)
        if 0 <= self._selected_index < len(items):
            # Temporarily disconnect to avoid triggering signal during initialization
            combo_box.setCurrentIndex(self._selected_index)

        # Set width
        width = self.parameter("width").value()
        combo_box.setMinimumWidth(width)

        # Connect signal AFTER setting initial value
        combo_box.currentIndexChanged.connect(
            lambda idx: self._on_selection_changed(idx, combo_box)
        )

        # Return both widget and signal data
        return {
            "widget": combo_box,
            "selected_index": self._selected_index,
            "selected_text": self._selected_text
        }

    def _on_selection_changed(self, index: int, combo_box: QComboBox):
        """Handle selection change in preview."""
        # Update signal data
        self._selected_index = index
        self._selected_text = combo_box.currentText()

        print(f"[Preview] {self.name}: Selected '{self._selected_text}' (index {index})")

        # Output to OutputPane if available
        try:
            from ...nodes.utils import print_output_signal
            print_output_signal.emit(self.name, f"Selected: '{self._selected_text}' (index {index})")
        except:
            pass
