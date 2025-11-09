"""
Math Nodes
==========

Basic mathematical operation nodes.
"""

from typing import Dict, Any
from ..base import BaseNode


class AddNode(BaseNode):
    """Node that adds two numbers."""

    category = "Math"
    description = "Add two numbers"

    def __init__(self, **kwargs):
        super().__init__(name="Add", node_type="AddNode", **kwargs)

    def setup(self) -> None:
        """Setup add node interface."""
        self.add_input("a", data_type="float", default_value=0.0, display_name="A")
        self.add_input("b", data_type="float", default_value=0.0, display_name="B")
        self.add_output("result", data_type="float", display_name="Result")

    def compute(self, **inputs) -> Dict[str, Any]:
        """Add a and b."""
        a = inputs.get("a", 0.0)
        b = inputs.get("b", 0.0)
        return {"result": a + b}


class SubtractNode(BaseNode):
    """Node that subtracts two numbers."""

    category = "Math"
    description = "Subtract two numbers"

    def __init__(self, **kwargs):
        super().__init__(name="Subtract", node_type="SubtractNode", **kwargs)

    def setup(self) -> None:
        """Setup subtract node interface."""
        self.add_input("a", data_type="float", default_value=0.0, display_name="A")
        self.add_input("b", data_type="float", default_value=0.0, display_name="B")
        self.add_output("result", data_type="float", display_name="Result")

    def compute(self, **inputs) -> Dict[str, Any]:
        """Subtract b from a."""
        a = inputs.get("a", 0.0)
        b = inputs.get("b", 0.0)
        return {"result": a - b}


class MultiplyNode(BaseNode):
    """Node that multiplies two numbers."""

    category = "Math"
    description = "Multiply two numbers"

    def __init__(self, **kwargs):
        super().__init__(name="Multiply", node_type="MultiplyNode", **kwargs)

    def setup(self) -> None:
        """Setup multiply node interface."""
        self.add_input("a", data_type="float", default_value=1.0, display_name="A")
        self.add_input("b", data_type="float", default_value=1.0, display_name="B")
        self.add_output("result", data_type="float", display_name="Result")

    def compute(self, **inputs) -> Dict[str, Any]:
        """Multiply a and b."""
        a = inputs.get("a", 1.0)
        b = inputs.get("b", 1.0)
        return {"result": a * b}


class DivideNode(BaseNode):
    """Node that divides two numbers."""

    category = "Math"
    description = "Divide two numbers"

    def __init__(self, **kwargs):
        super().__init__(name="Divide", node_type="DivideNode", **kwargs)

    def setup(self) -> None:
        """Setup divide node interface."""
        self.add_input("a", data_type="float", default_value=1.0, display_name="A")
        self.add_input("b", data_type="float", default_value=1.0, display_name="B")
        self.add_output("result", data_type="float", display_name="Result")

    def compute(self, **inputs) -> Dict[str, Any]:
        """Divide a by b."""
        a = inputs.get("a", 1.0)
        b = inputs.get("b", 1.0)

        if b == 0:
            print(f"Warning: Division by zero in node '{self.name}'")
            return {"result": 0.0}

        return {"result": a / b}
