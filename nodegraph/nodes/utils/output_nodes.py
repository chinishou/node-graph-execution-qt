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

        if prefix:
            output = f"{prefix}: {value}"
        else:
            output = str(value)

        # Emit to global signal for UI capture
        print_output_signal.emit(self.name, output)

        return {}


class DisplayNode(BaseNode):
    """Node that displays its input value without printing."""

    category: str = "Utils"
    description: str = "Display value (for inspection)"

    def __init__(self, **kwargs):
        super().__init__(name="Display", node_type="DisplayNode", **kwargs)

    def setup(self) -> None:
        """Setup display node interface."""
        self.add_input("value", data_type="any", default_value=None, label="Value")
        self.add_output("value", data_type="any", label="Value")

    def compute(self, **inputs) -> Dict[str, Any]:
        """Pass through the value."""
        value = inputs.get("value")
        return {"value": value}
