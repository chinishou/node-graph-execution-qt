"""
Node Graph Execution Qt
=======================

Houdini-style node-based programming framework for PySide6/PyQt6.

Basic usage (core only)::

    from nodegraph import NetworkModel, NodeModel
    from nodegraph.nodes.operators import AddNode
    from nodegraph.core.registry import NodeRegistry

    # Register and create nodes
    NodeRegistry.register(AddNode)
    network = NetworkModel("My Network")
    node = NodeRegistry.create_node("AddNode")
    network.add_node(node)

With Qt GUI (requires qt extra)::

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

# Core imports (always available)
from .core.models import NetworkModel, NodeModel, ParameterModel, ConnectorModel
from .core.registry import NodeRegistry
from .core.serialization import JSONSerializer, PythonExporter
from .nodes.base import BaseNode, PythonNode

# View layer imports (requires Qt)
# These will be imported when views are implemented
# from .views.widgets import NetworkEditor

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__license__",
    # Core models
    "NetworkModel",
    "NodeModel",
    "ParameterModel",
    "ConnectorModel",
    # Registry
    "NodeRegistry",
    # Serialization
    "JSONSerializer",
    "PythonExporter",
    # Base nodes
    "BaseNode",
    "PythonNode",
    # View layer (to be added)
    # "NetworkEditor",
]
