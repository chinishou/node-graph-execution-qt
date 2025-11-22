"""
Convert Node
============

Node for converting between different data types (int, bool, float, str).
"""

from typing import Dict, Any
from ..base import BaseNode


class ConvertNode(BaseNode):
    """Node that converts values between different data types."""

    category: str = "Operators"
    description: str = "Convert value to different data type"

    def __init__(self, **kwargs):
        super().__init__(name="Convert", node_type="ConvertNode", **kwargs)

    def setup(self) -> None:
        """Setup convert node interface."""
        # Input accepts any type
        self.add_input("value", data_type="any", default_value=0, label="Value")

        # Parameter to select output type
        self.add_parameter(
            "output_type",
            data_type="str",
            default_value="float",
            label="Output Type",
            menu_items=["int", "float", "bool", "str"]
        )

        # Output type matches the parameter selection
        self.add_output("result", data_type="any", label="Result")

    def compute(self, **inputs) -> Dict[str, Any]:
        """Convert input value to selected output type."""
        value = inputs.get("value", 0)
        output_type = self.parameter("output_type").value()

        try:
            # Use Python's built-in type conversion
            if output_type == "int":
                result = int(value)
            elif output_type == "float":
                result = float(value)
            elif output_type == "bool":
                result = bool(value)
            elif output_type == "str":
                result = str(value)
            else:
                # Fallback: no conversion
                result = value

            return {"result": result}

        except (ValueError, TypeError) as e:
            print(f"Warning: Conversion failed in node '{self.name}': {e}")
            # Return original value if conversion fails
            return {"result": value}

    def transforms_data_type(self) -> bool:
        """ConvertNode transforms data types between input and output."""
        return True
