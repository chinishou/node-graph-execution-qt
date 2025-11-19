#!/usr/bin/env python3
"""
Run Node Graph Editor
=====================

Launch the node graph editor application.
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from nodegraph.views import MainWindow


def main():
    """Main entry point."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Node Graph Editor")
    app.setOrganizationName("NodeGraph")

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
