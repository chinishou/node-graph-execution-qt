"""
Output Nodes
============

Nodes for outputting and displaying data.
"""

from typing import Dict, Any
from ..base import BaseNode
from ...core.signals import Signal


# Global signal for print output
print_output_signal = Signal()


class PrintNode(BaseNode):
    """Node that prints its input value."""

    category: str = "Utils"
    description: str = "Print value to output console"

    def __init__(self, **kwargs):
        super().__init__(name="Print", node_type="PrintNode", **kwargs)

    def setup(self) -> None:
        """Setup print node interface."""
        self.add_input("value", data_type="any", default_value=None, label="Value")
        self.add_parameter("prefix", data_type="string", default_value="", label="Prefix")

    def compute(self, **inputs) -> Dict[str, Any]:
        """Print the input value."""
        value = inputs.get("value")
        prefix = self.parameter("prefix").value()

        # Get full node path
        node_path = self.get_path()

        if prefix:
            output = f"{prefix}: {value}"
        else:
            output = str(value)

        # Emit to global signal for UI capture with full path
        print_output_signal.emit(node_path, output)

        return {}
