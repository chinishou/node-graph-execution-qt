"""
Node Graph Execution Qt
=======================

Houdini-style node-based programming framework for PySide6/PyQt6.

Basic usage::

    from nodegraph import NetworkEditor
    from qtpy.QtWidgets import QApplication

    app = QApplication([])
    editor = NetworkEditor()
    editor.show()
    app.exec()
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__license__ = "MIT"

# Core imports will be added as we implement them
# from .core.models import NetworkModel, NodeModel, ParameterModel, ConnectorModel
# from .nodes.base import BaseNode
# from .views.widgets import NetworkEditor

__all__ = [
    "__version__",
    # "NetworkModel",
    # "NodeModel",
    # "ParameterModel",
    # "ConnectorModel",
    # "BaseNode",
    # "NetworkEditor",
]
