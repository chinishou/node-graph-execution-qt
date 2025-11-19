"""
Output Pane
===========

Widget for displaying print output from nodes.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QTextCursor, QColor

from typing import TYPE_CHECKING
from datetime import datetime


class OutputPane(QWidget):
    """
    Widget for displaying output from PrintNode and other nodes.

    Shows timestamped output with node names.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self._setup_ui()

    def _setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header
        header_layout = QHBoxLayout()

        header_label = QLabel("Output")
        header_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #dcdcdc;
            }
        """)
        header_layout.addWidget(header_label)

        header_layout.addStretch()

        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear)
        header_layout.addWidget(clear_btn)

        layout.addLayout(header_layout)

        # Output text area
        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setLineWrapMode(QTextEdit.NoWrap)
        layout.addWidget(self._output)

        # Style
        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                color: #dcdcdc;
            }
            QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                font-family: monospace;
                font-size: 11px;
            }
            QPushButton {
                background-color: #4a4a4a;
                border: 1px solid #5a5a5a;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
            }
        """)

    @Slot(str, str)
    def append_output(self, node_name: str, text: str):
        """Append output text from a node."""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Format: [time] node_name: text
        formatted = f'<span style="color: #808080;">[{timestamp}]</span> '
        formatted += f'<span style="color: #80b0ff;">{node_name}</span>: '
        formatted += f'<span style="color: #dcdcdc;">{text}</span>'

        self._output.append(formatted)

        # Scroll to bottom
        cursor = self._output.textCursor()
        cursor.movePosition(QTextCursor.End)
        self._output.setTextCursor(cursor)

    def append_info(self, text: str):
        """Append info message."""
        timestamp = datetime.now().strftime("%H:%M:%S")

        formatted = f'<span style="color: #808080;">[{timestamp}]</span> '
        formatted += f'<span style="color: #80ff80;">{text}</span>'

        self._output.append(formatted)

    def append_error(self, text: str):
        """Append error message."""
        timestamp = datetime.now().strftime("%H:%M:%S")

        formatted = f'<span style="color: #808080;">[{timestamp}]</span> '
        formatted += f'<span style="color: #ff8080;">{text}</span>'

        self._output.append(formatted)

    def clear(self):
        """Clear all output."""
        self._output.clear()

    def get_text(self) -> str:
        """Get all output text."""
        return self._output.toPlainText()
