"""
Math Nodes
==========

Basic mathematical operation nodes.
"""

from typing import Dict, Any
from ..base import BaseNode


class AddNode(BaseNode):
    """Node that adds two numbers."""

    category: str = "Math"
    description: str = "Add two numbers"

    def __init__(self, **kwargs):
        super().__init__(name="Add", node_type="AddNode", **kwargs)

    def setup(self) -> None:
        """Setup add node interface."""
        self.add_parameter(
            "type",
            data_type="str",
            default_value="float",
            label="Type",
            menu_items=["int", "float"]
        )
        self.add_input("a", data_type="any", default_value=0.0, label="A")
        self.add_input("b", data_type="any", default_value=0.0, label="B")
        self.add_output("result", data_type="any", label="Result")

    def compute(self, **inputs) -> Dict[str, Any]:
        """Add a and b."""
        a = inputs.get("a", 0.0)
        b = inputs.get("b", 0.0)
        value_type = self.parameter("type").value()

        result = a + b

        # Convert to selected type
        if value_type == "int":
            result = int(result)
        else:
            result = float(result)

        return {"result": result}


class SubtractNode(BaseNode):
    """Node that subtracts two numbers."""

    category: str = "Math"
    description: str = "Subtract two numbers"

    def __init__(self, **kwargs):
        super().__init__(name="Subtract", node_type="SubtractNode", **kwargs)

    def setup(self) -> None:
        """Setup subtract node interface."""
        self.add_parameter(
            "type",
            data_type="str",
            default_value="float",
            label="Type",
            menu_items=["int", "float"]
        )
        self.add_input("a", data_type="any", default_value=0.0, label="A")
        self.add_input("b", data_type="any", default_value=0.0, label="B")
        self.add_output("result", data_type="any", label="Result")

    def compute(self, **inputs) -> Dict[str, Any]:
        """Subtract b from a."""
        a = inputs.get("a", 0.0)
        b = inputs.get("b", 0.0)
        value_type = self.parameter("type").value()

        result = a - b

        # Convert to selected type
        if value_type == "int":
            result = int(result)
        else:
            result = float(result)

        return {"result": result}


class MultiplyNode(BaseNode):
    """Node that multiplies two numbers."""

    category: str = "Math"
    description: str = "Multiply two numbers"

    def __init__(self, **kwargs):
        super().__init__(name="Multiply", node_type="MultiplyNode", **kwargs)

    def setup(self) -> None:
        """Setup multiply node interface."""
        self.add_parameter(
            "type",
            data_type="str",
            default_value="float",
            label="Type",
            menu_items=["int", "float"]
        )
        self.add_input("a", data_type="any", default_value=1.0, label="A")
        self.add_input("b", data_type="any", default_value=1.0, label="B")
        self.add_output("result", data_type="any", label="Result")

    def compute(self, **inputs) -> Dict[str, Any]:
        """Multiply a and b."""
        a = inputs.get("a", 1.0)
        b = inputs.get("b", 1.0)
        value_type = self.parameter("type").value()

        result = a * b

        # Convert to selected type
        if value_type == "int":
            result = int(result)
        else:
            result = float(result)

        return {"result": result}


class DivideNode(BaseNode):
    """Node that divides two numbers."""

    category: str = "Math"
    description: str = "Divide two numbers"

    def __init__(self, **kwargs):
        super().__init__(name="Divide", node_type="DivideNode", **kwargs)

    def setup(self) -> None:
        """Setup divide node interface."""
        self.add_parameter(
            "type",
            data_type="str",
            default_value="float",
            label="Type",
            menu_items=["int", "float"]
        )
        self.add_input("a", data_type="any", default_value=1.0, label="A")
        self.add_input("b", data_type="any", default_value=1.0, label="B")
        self.add_output("result", data_type="any", label="Result")

    def compute(self, **inputs) -> Dict[str, Any]:
        """Divide a by b."""
        a = inputs.get("a", 1.0)
        b = inputs.get("b", 1.0)
        value_type = self.parameter("type").value()

        if b == 0:
            print(f"Warning: Division by zero in node '{self.name}'")
            return {"result": 0}

        result = a / b

        # Convert to selected type
        if value_type == "int":
            result = int(result)
        else:
            result = float(result)

        return {"result": result}
