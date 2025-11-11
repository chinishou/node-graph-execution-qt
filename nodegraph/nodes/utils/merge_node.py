"""
Merge Node
==========

Node for merging multiple inputs into a list.
Similar to Houdini's merge node.
"""

from typing import Dict, Any
from ..base import BaseNode


class MergeNode(BaseNode):
    """
    Merge node for combining multiple inputs into a list.

    This node accepts multiple connections on its input and outputs them as a list.
    Similar to Houdini's merge node, this allows you to:
    - Combine multiple values into a list
    - Collect results from multiple nodes
    - Create arrays/lists dynamically

    Example::

        # Create some variable nodes
        var1 = FloatVariable(default_value=1.0)
        var2 = FloatVariable(default_value=2.0)
        var3 = FloatVariable(default_value=3.0)

        # Merge them into a list
        merge = MergeNode()
        var1.output("out").connect_to(merge.input("items"))
        var2.output("out").connect_to(merge.input("items"))
        var3.output("out").connect_to(merge.input("items"))

        # Result: merge.output("list") = [1.0, 2.0, 3.0]
    """

    category = "Utils"
    description = "Merge multiple inputs into a list"

    def __init__(self, **kwargs):
        super().__init__(
            name="Merge",
            node_type="MergeNode",
            **kwargs
        )

    def setup(self) -> None:
        """Setup merge node interface."""
        # Multi-connection input accepts any number of connections
        self.add_input(
            "items",
            data_type="any",
            multi_connection=True,  # Key: allows multiple connections
            display_name="Items",
            description="Connect multiple outputs here to merge into a list"
        )

        # Output as list
        self.add_output(
            "list",
            data_type="any",  # List of any type
            display_name="List",
            description="Merged list of all connected inputs"
        )

    def compute(self, **inputs) -> Dict[str, Any]:
        """
        Merge all connected inputs into a list.

        The input "items" will be a list due to multi_connection=True.
        """
        items = inputs.get("items", [])  # Already a list!

        return {"list": items}


class TypedMergeNode(BaseNode):
    """
    Typed merge node for combining multiple inputs of the same type.

    Unlike MergeNode, this node enforces type consistency.
    """

    category = "Utils"
    description = "Merge multiple inputs of the same type into a list"

    def __init__(self, data_type: str = "float", **kwargs):
        """
        Initialize typed merge node.

        Args:
            data_type: Type to enforce for all inputs
            **kwargs: Additional arguments
        """
        self._input_data_type = data_type
        super().__init__(
            name=f"Merge {data_type.capitalize()}",
            node_type="TypedMergeNode",
            **kwargs
        )

    def setup(self) -> None:
        """Setup typed merge node interface."""
        # Multi-connection input with specific type
        self.add_input(
            "items",
            data_type=self._input_data_type,
            multi_connection=True,
            display_name=f"{self._input_data_type.capitalize()} Items",
            description=f"Connect multiple {self._input_data_type} outputs here"
        )

        # Output as list
        self.add_output(
            "list",
            data_type="any",  # Python list
            display_name="List",
            description=f"List of {self._input_data_type} values"
        )

    def compute(self, **inputs) -> Dict[str, Any]:
        """Merge all inputs into a typed list."""
        items = inputs.get("items", [])
        return {"list": items}
