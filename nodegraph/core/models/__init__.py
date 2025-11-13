"""
Core data models
================

Data models for the node graph system.
These are pure Python classes without Qt dependencies.
"""

from .parameter_model import ParameterModel
from .connector_model import ConnectorModel, ConnectorType
from .node_model import NodeModel
from .network_model import NetworkModel

# Rebuild Pydantic models to resolve forward references
NodeModel.model_rebuild()
ConnectorModel.model_rebuild()

__all__ = [
    "ParameterModel",
    "ConnectorModel",
    "ConnectorType",
    "NodeModel",
    "NetworkModel",
]
