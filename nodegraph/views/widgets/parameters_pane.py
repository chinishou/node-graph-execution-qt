"""
Parameters Pane
===============

Widget for displaying and editing node parameters.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QDoubleSpinBox, QCheckBox, QScrollArea, QFrame,
    QGroupBox, QPushButton, QComboBox
)
from PySide6.QtCore import Qt, Signal

from typing import TYPE_CHECKING, Optional, Dict, Any

if TYPE_CHECKING:
    from ...core.models import NodeModel, ParameterModel, ConnectorModel


class ParametersPane(QWidget):
    """
    Widget for displaying and editing node parameters.

    Shows:
    - Node name
    - Input default values
    - Parameters
    """

    # Signals
    parameter_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._node: Optional["NodeModel"] = None
        self._widgets: Dict[str, QWidget] = {}
        self._labels: Dict[str, QLabel] = {}  # Store labels for styling updates

        self._setup_ui()

    def _setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header
        self._header_label = QLabel("No Selection")
        self._header_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #dcdcdc;
                padding: 4px;
            }
        """)
        layout.addWidget(self._header_label)

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Content widget
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(8)
        self._content_layout.addStretch()

        scroll.setWidget(self._content)
        layout.addWidget(scroll)

        # Execute button
        self._execute_btn = QPushButton("Execute")
        self._execute_btn.clicked.connect(self._on_execute)
        self._execute_btn.setEnabled(False)
        layout.addWidget(self._execute_btn)

        # Style
        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                color: #dcdcdc;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox {
                background-color: #3c3c3c;
                border: 1px solid #4c4c4c;
                border-radius: 3px;
                padding: 4px;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 1px solid #6c6c6c;
            }
            QPushButton {
                background-color: #4a4a4a;
                border: 1px solid #5a5a5a;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
            }
            QPushButton:disabled {
                background-color: #3a3a3a;
                color: #6a6a6a;
            }
        """)

    def set_node(self, node: Optional["NodeModel"]):
        """Set the node to display."""
        self._node = node
        self._widgets.clear()
        self._labels.clear()

        # Clear content
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not node:
            self._header_label.setText("No Selection")
            self._execute_btn.setEnabled(False)
            return

        # Update header
        self._header_label.setText(f"{node.name} ({node.node_type})")
        self._execute_btn.setEnabled(True)

        # Create input defaults group
        inputs = node.inputs()
        if inputs:
            group = QGroupBox("Input Defaults")
            group_layout = QVBoxLayout(group)

            for name, connector in inputs.items():
                widget = self._create_connector_widget(connector)
                group_layout.addWidget(widget)

                # Connect signal to update enabled state when connection changes
                connector.connected_changed.connect(
                    lambda c=connector: self._on_connector_connection_changed(c)
                )

            self._content_layout.insertWidget(
                self._content_layout.count() - 1, group
            )

        # Create parameters group
        params = node.parameters()
        if params:
            group = QGroupBox("Parameters")
            group_layout = QVBoxLayout(group)

            for name, param in params.items():
                widget = self._create_parameter_widget(param)
                group_layout.addWidget(widget)

            self._content_layout.insertWidget(
                self._content_layout.count() - 1, group
            )

        # Create outputs group (read-only display)
        outputs = node.outputs()
        if outputs:
            group = QGroupBox("Outputs")
            group_layout = QVBoxLayout(group)

            for name, connector in outputs.items():
                widget = self._create_output_widget(connector)
                group_layout.addWidget(widget)

            self._content_layout.insertWidget(
                self._content_layout.count() - 1, group
            )

    def _create_connector_widget(self, connector: "ConnectorModel") -> QWidget:
        """Create widget for editing connector default value."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 2, 0, 2)

        # Label
        label = QLabel(connector.label or connector.name)
        label.setMinimumWidth(80)
        layout.addWidget(label)

        # Editor
        editor = self._create_value_editor(
            connector.data_type,
            connector.default_value,
            lambda v: self._on_connector_value_changed(connector, v)
        )
        layout.addWidget(editor)

        # Store widgets for later updates
        self._widgets[f"input_{connector.name}"] = editor
        self._labels[f"input_{connector.name}"] = label

        # Apply initial style based on connection state
        is_connected = connector.is_connected()
        editor.setEnabled(not is_connected)
        if is_connected:
            label.setStyleSheet("color: #888888; font-style: italic;")
            editor.setStyleSheet("background-color: #1a1a1a; color: #666666;")
        else:
            label.setStyleSheet("")
            editor.setStyleSheet("")

        return widget

    def _create_parameter_widget(self, param: "ParameterModel") -> QWidget:
        """Create widget for editing parameter value."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 2, 0, 2)

        # Label
        label = QLabel(param.label or param.name)
        label.setMinimumWidth(80)
        layout.addWidget(label)

        # Editor - check if parameter has menu_items (dropdown)
        if param.menu_items and len(param.menu_items) > 0:
            # Create combo box for menu selection
            editor = QComboBox()
            for item in param.menu_items:
                editor.addItem(str(item))

            # Set current value
            current_value = str(param.value())
            index = editor.findText(current_value)
            if index >= 0:
                editor.setCurrentIndex(index)

            # Connect signal
            editor.currentTextChanged.connect(
                lambda v: self._on_parameter_value_changed(param, v)
            )
        else:
            # Use standard value editor
            editor = self._create_value_editor(
                param.data_type,
                param.value(),
                lambda v: self._on_parameter_value_changed(param, v)
            )

        layout.addWidget(editor)
        self._widgets[f"param_{param.name}"] = editor

        return widget

    def _create_output_widget(self, connector: "ConnectorModel") -> QWidget:
        """Create widget for displaying output value."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 2, 0, 2)

        # Label
        label = QLabel(connector.label or connector.name)
        label.setMinimumWidth(80)
        layout.addWidget(label)

        # Value display
        value_label = QLabel("--")
        value_label.setStyleSheet("color: #8a8a8a;")
        layout.addWidget(value_label)

        self._widgets[f"output_{connector.name}"] = value_label

        return widget

    def _create_value_editor(self, data_type: str, value: Any, callback) -> QWidget:
        """Create appropriate editor widget for data type."""
        if data_type == "int":
            editor = QSpinBox()
            editor.setRange(-999999, 999999)
            editor.setValue(int(value) if value is not None else 0)
            editor.valueChanged.connect(callback)
            editor.setButtonSymbols(QSpinBox.NoButtons)  # Remove up/down buttons

        elif data_type == "float":
            editor = QDoubleSpinBox()
            editor.setRange(-999999.0, 999999.0)
            editor.setDecimals(4)
            editor.setValue(float(value) if value is not None else 0.0)
            editor.valueChanged.connect(callback)
            editor.setButtonSymbols(QDoubleSpinBox.NoButtons)  # Remove up/down buttons

        elif data_type == "bool":
            editor = QCheckBox()
            editor.setChecked(bool(value) if value is not None else False)
            editor.stateChanged.connect(lambda s: callback(s == Qt.Checked))

        else:  # string or any
            editor = QLineEdit()
            editor.setText(str(value) if value is not None else "")
            editor.textChanged.connect(callback)

        return editor

    def _on_connector_value_changed(self, connector: "ConnectorModel", value: Any):
        """Handle connector default value change."""
        connector.default_value = value
        self.parameter_changed.emit()

    def _on_parameter_value_changed(self, param: "ParameterModel", value: Any):
        """Handle parameter value change."""
        param.set_value(value)
        self.parameter_changed.emit()

    def _on_connector_connection_changed(self, connector: "ConnectorModel"):
        """Handle connector connection state change."""
        # Update the enabled state and appearance of the corresponding input widget
        widget_key = f"input_{connector.name}"
        if widget_key in self._widgets:
            editor = self._widgets[widget_key]
            label = self._labels.get(widget_key)

            is_connected = connector.is_connected()
            # Disable if connected, enable if disconnected
            editor.setEnabled(not is_connected)

            # Update visual appearance
            if is_connected:
                # Connected: gray out and italicize
                if label:
                    label.setStyleSheet("color: #888888; font-style: italic;")
                editor.setStyleSheet("background-color: #1a1a1a; color: #666666;")
            else:
                # Disconnected: restore normal appearance
                if label:
                    label.setStyleSheet("")
                editor.setStyleSheet("")

    def _on_execute(self):
        """Execute the current node."""
        if self._node:
            success = self._node.execute()

            if success:
                # Update output displays
                self._update_output_displays()

    def _update_output_displays(self):
        """Update output value displays."""
        if not self._node:
            return

        for name, connector in self._node.outputs().items():
            widget = self._widgets.get(f"output_{name}")
            if widget and isinstance(widget, QLabel):
                value = self._node.get_output_value(name)
                widget.setText(str(value) if value is not None else "--")

    def refresh(self):
        """Refresh the display."""
        if self._node:
            self.set_node(self._node)
