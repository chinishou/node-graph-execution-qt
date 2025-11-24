"""
UI Root Node
============

Entry point node for UI preview system.
"""

from typing import Dict, Any
from ..base import BaseNode


class UIRootNode(BaseNode):
    """
    UI Root Node - Entry point for live UI preview.

    The LivePreviewPane looks for this node in the network and
    uses its output widget as the root of the preview.

    Connect other UI widgets to this node's input to preview them.
    """

    category: str = "UI"
    description: str = "Entry point for UI preview"

    def __init__(self, **kwargs):
        super().__init__(
            name="UI Root",
            node_type="UIRootNode",
            **kwargs
        )

    def setup(self) -> None:
        """Setup inputs and outputs."""
        self.add_input("widget", data_type="widget", label="Root Widget")
        self.add_output("widget", data_type="widget", label="Widget")

    def compute(self, **inputs) -> Dict[str, Any]:
        """Pass through the input widget."""
        widget = inputs.get("widget")
        return {"widget": widget}
