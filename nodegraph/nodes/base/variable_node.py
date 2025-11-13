"""
Variable Node
=============

Node for declaring and outputting constant values.
Similar to Houdini's parameter node or constant node.
"""

from typing import Dict, Any
from .base_node import BaseNode
from ...core.data_types import DataTypeRegistry


class VariableNode(BaseNode):
    """
    Variable node for declaring constant values.

    This node has no inputs - it only has a parameter that defines a value
    and an output that provides that value to other nodes.

    Similar to Houdini's parameter node, this allows you to:
    - Declare constants in your graph
    - Create reusable values that can be changed in one place
    - Organize your graph with named variables

    Example::

        # Create a float variable
        var = VariableNode(data_type="float")
        var.parameter("value").set_value(3.14)

        # Create a string variable
        text = VariableNode(data_type="str", name="Message")
        text.parameter("value").set_value("Hello World")

        # Connect to other nodes
        add = AddNode()
        var.output("out").connect_to(add.input("a"))
    """

    category = "Variables"
    description = "Output a constant value"

    def __init__(
        self,
        data_type: str = "float",
        default_value: Any = None,
        name: str = "Variable",
        **kwargs
    ):
        """
        Initialize variable node.

        Args:
            data_type: Data type for the variable (int, float, str, bool, or custom)
            default_value: Initial value (uses type default if None)
            name: Node name
            **kwargs: Additional arguments passed to BaseNode
        """
        self._data_type = data_type
        self._default_value = default_value

        super().__init__(
            name=name,
            node_type="VariableNode",
            **kwargs
        )

    def setup(self) -> None:
        """Setup variable node interface."""
        # Get default value from DataTypeRegistry if not provided
        if self._default_value is None:
            self._default_value = DataTypeRegistry.get_default_value(self._data_type)

        # Add parameter for the value
        self.add_parameter(
            "value",
            data_type=self._data_type,
            default_value=self._default_value,
            display_name="Value",
            description=f"The {self._data_type} value to output"
        )

        # Add output (same type as parameter)
        self.add_output(
            "out",
            data_type=self._data_type,
            display_name="Output",
            description="Outputs the parameter value"
        )

    def compute(self, **inputs) -> Dict[str, Any]:
        """
        Output the parameter value.

        No inputs are needed - just returns the parameter value.
        """
        value = self.parameter("value").value()
        return {"out": value}


class IntVariable(VariableNode):
    """Integer variable node."""

    def __init__(self, default_value: int = 0, **kwargs):
        super().__init__(
            data_type="int",
            default_value=default_value,
            name=kwargs.pop("name", "Int"),
            **kwargs
        )


class FloatVariable(VariableNode):
    """Float variable node."""

    def __init__(self, default_value: float = 0.0, **kwargs):
        super().__init__(
            data_type="float",
            default_value=default_value,
            name=kwargs.pop("name", "Float"),
            **kwargs
        )


class StringVariable(VariableNode):
    """String variable node."""

    def __init__(self, default_value: str = "", **kwargs):
        super().__init__(
            data_type="str",
            default_value=default_value,
            name=kwargs.pop("name", "String"),
            **kwargs
        )


class BoolVariable(VariableNode):
    """Boolean variable node."""

    def __init__(self, default_value: bool = False, **kwargs):
        super().__init__(
            data_type="bool",
            default_value=default_value,
            name=kwargs.pop("name", "Bool"),
            **kwargs
        )
