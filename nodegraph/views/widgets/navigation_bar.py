"""
Navigation Bar
==============

UI widget for displaying and navigating the network hierarchy.
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QToolButton, QLabel, QPushButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from ...core.navigation import NavigationController


class NavigationBar(QWidget):
    """
    Navigation bar widget showing current location and providing navigation controls.

    Features:
    - Back/forward buttons
    - Breadcrumb path (clickable)
    - Up button
    """

    # Signals
    navigate_requested = Signal(int)  # Navigate to depth

    def __init__(self, navigation_controller: "NavigationController" = None, parent=None):
        super().__init__(parent)

        self._navigation_controller = navigation_controller

        self._setup_ui()

        # Connect to navigation controller
        if self._navigation_controller:
            self._connect_controller()
            self._update_ui()

    def _setup_ui(self):
        """Setup the UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(2)

        # Back button
        self._back_button = QToolButton()
        self._back_button.setText("◄")
        self._back_button.setToolTip("Go Back (Alt+Left)")
        self._back_button.clicked.connect(self._on_back_clicked)
        layout.addWidget(self._back_button)

        # Forward button
        self._forward_button = QToolButton()
        self._forward_button.setText("►")
        self._forward_button.setToolTip("Go Forward (Alt+Right)")
        self._forward_button.clicked.connect(self._on_forward_clicked)
        layout.addWidget(self._forward_button)

        # Up button
        self._up_button = QToolButton()
        self._up_button.setText("▲")
        self._up_button.setToolTip("Go Up (U)")
        self._up_button.clicked.connect(self._on_up_clicked)
        layout.addWidget(self._up_button)

        # Separator
        layout.addSpacing(10)

        # Path container
        self._path_widget = QWidget()
        self._path_layout = QHBoxLayout(self._path_widget)
        self._path_layout.setContentsMargins(0, 0, 0, 0)
        self._path_layout.setSpacing(0)
        layout.addWidget(self._path_widget)

        # Stretch to push everything to the left
        layout.addStretch()

    def set_navigation_controller(self, controller: "NavigationController"):
        """Set the navigation controller."""
        self._navigation_controller = controller
        self._connect_controller()
        self._update_ui()

    def _connect_controller(self):
        """Connect to navigation controller signals."""
        if not self._navigation_controller:
            return

        self._navigation_controller.location_changed.connect(self._update_ui)
        self._navigation_controller.can_go_back_changed.connect(self._update_buttons)
        self._navigation_controller.can_go_forward_changed.connect(self._update_buttons)

    def _update_ui(self):
        """Update the entire UI."""
        self._update_buttons()
        self._update_path()

    def _update_buttons(self, _=None):
        """Update button states."""
        if not self._navigation_controller:
            self._back_button.setEnabled(False)
            self._forward_button.setEnabled(False)
            self._up_button.setEnabled(False)
            return

        self._back_button.setEnabled(self._navigation_controller.can_go_back())
        self._forward_button.setEnabled(self._navigation_controller.can_go_forward())

        # Up button enabled if not at root
        location = self._navigation_controller.get_current_location()
        self._up_button.setEnabled(location.get_depth() > 0)

    def _update_path(self):
        """Update the breadcrumb path display."""
        # Clear existing path
        while self._path_layout.count():
            item = self._path_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._navigation_controller:
            return

        # Get path components
        components = self._navigation_controller.get_path_components()

        for i, (name, depth) in enumerate(components):
            # Add separator if not first
            if i > 0:
                separator = QLabel(" → ")
                separator.setStyleSheet("color: #888;")
                self._path_layout.addWidget(separator)

            # Add clickable path component
            button = QPushButton(name)
            button.setFlat(True)
            button.setCursor(Qt.PointingHandCursor)
            button.setStyleSheet("""
                QPushButton {
                    border: none;
                    padding: 2px 8px;
                    text-align: left;
                    color: #CCC;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                    color: #FFF;
                }
                QPushButton:pressed {
                    background-color: rgba(255, 255, 255, 0.2);
                }
            """)

            # Connect to navigate to this depth
            button.clicked.connect(lambda checked=False, d=depth: self._navigate_to_depth(d))

            # Highlight current location
            if i == len(components) - 1:
                button.setStyleSheet(button.styleSheet() + """
                    QPushButton {
                        color: #6AF;
                        font-weight: bold;
                    }
                """)

            self._path_layout.addWidget(button)

    def _on_back_clicked(self):
        """Handle back button click."""
        if self._navigation_controller:
            self._navigation_controller.go_back()

    def _on_forward_clicked(self):
        """Handle forward button click."""
        if self._navigation_controller:
            self._navigation_controller.go_forward()

    def _on_up_clicked(self):
        """Handle up button click."""
        if self._navigation_controller:
            self._navigation_controller.go_up()

    def _navigate_to_depth(self, depth: int):
        """Navigate to a specific depth."""
        if self._navigation_controller:
            self._navigation_controller.navigate_to_depth(depth)
