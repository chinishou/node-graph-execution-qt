"""
Layout Nodes
============

Nodes for creating layout containers.
"""

from typing import Dict, Any
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QMainWindow
from ..base import BaseNode


class VBoxLayoutNode(BaseNode):
    """
    VBox Layout Node - Creates a vertical box layout.

    Arranges child widgets vertically from top to bottom.
    Number of inputs controlled by 'num_children' parameter.
    """

    category: str = "UI/Layouts"
    description: str = "Vertical box layout"

    def __init__(self, num_children: int = 5, **kwargs):
        # Pass _setup_ parameters via kwargs to BaseNode
        super().__init__(
            name="VBox Layout",
            node_type="VBoxLayoutNode",
            _setup_num_children=num_children,
            **kwargs
        )

    def setup(self) -> None:
        """Setup inputs, parameters, and outputs."""
        # Parameter to control number of children
        # Safe guard for backwards compatibility
        if not hasattr(self, '_setup_num_children'):
            self._setup_num_children = 5
        self.add_parameter("num_children", data_type="int",
                          default_value=self._setup_num_children,
                          label="Num Children")

        # Layout parameters
        self.add_parameter("spacing", data_type="int", default_value=5, label="Spacing")
        self.add_parameter("margins", data_type="int", default_value=10, label="Margins")

        # Create inputs based on num_children parameter
        num_children = self.parameter("num_children").value()
        for i in range(1, num_children + 1):
            self.add_input(f"child{i}", data_type="widget", label=f"Child {i}")

        self.add_output("widget", data_type="widget", label="Container")

    def compute(self, **inputs) -> Dict[str, Any]:
        """Create the layout container."""
        # Create a fresh container each time (simple and safe for manual refresh)
        container = QWidget()
        layout = QVBoxLayout(container)

        # Set layout parameters
        spacing = self.parameter("spacing").value()
        margins = self.parameter("margins").value()

        layout.setSpacing(spacing)
        layout.setContentsMargins(margins, margins, margins, margins)

        # Add child widgets that are connected (dynamic based on num_children)
        num_children = self.parameter("num_children").value()
        for i in range(1, num_children + 1):
            child = inputs.get(f"child{i}")
            if child and isinstance(child, QWidget):
                # Set parent to our container
                child.setParent(container)
                layout.addWidget(child)

        # Add stretch at the end to push widgets to top
        layout.addStretch()

        return {"widget": container}


class HBoxLayoutNode(BaseNode):
    """
    HBox Layout Node - Creates a horizontal box layout.

    Arranges child widgets horizontally from left to right.
    Number of inputs controlled by 'num_children' parameter.
    """

    category: str = "UI/Layouts"
    description: str = "Horizontal box layout"

    def __init__(self, num_children: int = 5, **kwargs):
        # Pass _setup_ parameters via kwargs to BaseNode
        super().__init__(
            name="HBox Layout",
            node_type="HBoxLayoutNode",
            _setup_num_children=num_children,
            **kwargs
        )

    def setup(self) -> None:
        """Setup inputs, parameters, and outputs."""
        # Parameter to control number of children
        # Safe guard for backwards compatibility
        if not hasattr(self, '_setup_num_children'):
            self._setup_num_children = 5
        self.add_parameter("num_children", data_type="int",
                          default_value=self._setup_num_children,
                          label="Num Children")

        # Layout parameters
        self.add_parameter("spacing", data_type="int", default_value=5, label="Spacing")
        self.add_parameter("margins", data_type="int", default_value=10, label="Margins")

        # Create inputs based on num_children parameter
        num_children = self.parameter("num_children").value()
        for i in range(1, num_children + 1):
            self.add_input(f"child{i}", data_type="widget", label=f"Child {i}")

        self.add_output("widget", data_type="widget", label="Container")

    def compute(self, **inputs) -> Dict[str, Any]:
        """Create the layout container."""
        container = QWidget()
        layout = QHBoxLayout(container)

        # Set layout parameters
        spacing = self.parameter("spacing").value()
        margins = self.parameter("margins").value()

        layout.setSpacing(spacing)
        layout.setContentsMargins(margins, margins, margins, margins)

        # Add child widgets that are connected
        num_children = self.parameter("num_children").value()
        for i in range(1, num_children + 1):
            child = inputs.get(f"child{i}")
            if child and isinstance(child, QWidget):
                child.setParent(container)
                layout.addWidget(child)

        # Add stretch at the end
        layout.addStretch()

        return {"widget": container}


class QWidgetContainerNode(BaseNode):
    """
    QWidget Container Node - Creates a QWidget with layout.

    Generic container widget that can hold multiple children with layout.
    Number of inputs controlled by 'num_children' parameter.
    """

    category: str = "UI/Containers"
    description: str = "QWidget container"

    def __init__(self, num_children: int = 3, **kwargs):
        # Pass _setup_ parameters via kwargs to BaseNode
        super().__init__(
            name="QWidget Container",
            node_type="QWidgetContainerNode",
            _setup_num_children=num_children,
            **kwargs
        )

    def setup(self) -> None:
        """Setup inputs, parameters, and outputs."""
        # Parameter to control number of children
        # Safe guard for backwards compatibility
        if not hasattr(self, '_setup_num_children'):
            self._setup_num_children = 3
        self.add_parameter("num_children", data_type="int",
                          default_value=self._setup_num_children,
                          label="Num Children")

        # Choose layout type
        self.add_parameter("layout_type", data_type="str",
                          default_value="vbox",
                          label="Layout Type",
                          menu_items=["vbox", "hbox"])

        # Layout parameters
        self.add_parameter("spacing", data_type="int", default_value=5, label="Spacing")
        self.add_parameter("margins", data_type="int", default_value=10, label="Margins")

        # Create inputs based on num_children parameter
        num_children = self.parameter("num_children").value()
        for i in range(1, num_children + 1):
            self.add_input(f"child{i}", data_type="widget", label=f"Child {i}")

        self.add_output("widget", data_type="widget", label="Widget")

    def compute(self, **inputs) -> Dict[str, Any]:
        """Create the container widget."""
        container = QWidget()

        # Create layout based on layout_type parameter
        layout_type = self.parameter("layout_type").value()
        if layout_type == "hbox":
            layout = QHBoxLayout(container)
        else:  # vbox
            layout = QVBoxLayout(container)

        # Set layout parameters
        spacing = self.parameter("spacing").value()
        margins = self.parameter("margins").value()

        layout.setSpacing(spacing)
        layout.setContentsMargins(margins, margins, margins, margins)

        # Add child widgets
        num_children = self.parameter("num_children").value()
        for i in range(1, num_children + 1):
            child = inputs.get(f"child{i}")
            if child and isinstance(child, QWidget):
                child.setParent(container)
                layout.addWidget(child)

        layout.addStretch()

        return {"widget": container}


class QMainWindowNode(BaseNode):
    """
    QMainWindow Node - Creates a QMainWindow.

    Main window widget with central widget support.
    """

    category: str = "UI/Containers"
    description: str = "QMainWindow container"

    def __init__(self, **kwargs):
        super().__init__(
            name="QMainWindow",
            node_type="QMainWindowNode",
            **kwargs
        )

    def setup(self) -> None:
        """Setup inputs, parameters, and outputs."""
        self.add_input("central_widget", data_type="widget", label="Central Widget")
        self.add_parameter("title", data_type="str", default_value="My Window", label="Window Title")
        self.add_parameter("width", data_type="int", default_value=800, label="Width")
        self.add_parameter("height", data_type="int", default_value=600, label="Height")
        self.add_output("widget", data_type="widget", label="MainWindow")

    def compute(self, **inputs) -> Dict[str, Any]:
        """Create the main window."""
        main_window = QMainWindow()

        # Set window properties
        title = self.parameter("title").value()
        width = self.parameter("width").value()
        height = self.parameter("height").value()

        main_window.setWindowTitle(title)
        main_window.resize(width, height)

        # Set central widget if provided
        central_widget = inputs.get("central_widget")
        if central_widget and isinstance(central_widget, QWidget):
            main_window.setCentralWidget(central_widget)

        return {"widget": main_window}
