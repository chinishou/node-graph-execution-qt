"""
Core module - Data models and business logic
=============================================

This module contains the core data structures that are independent of Qt UI.
These models can be used in headless mode (CLI, testing, etc.).
"""

from .models import NetworkModel, NodeModel, ParameterModel, ConnectorModel

__all__ = [
    "NetworkModel",
    "NodeModel",
    "ParameterModel",
    "ConnectorModel",
]
