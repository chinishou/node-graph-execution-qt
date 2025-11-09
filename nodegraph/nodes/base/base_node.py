"""
Base Node
=========

Base class for all nodes. Users should inherit from this class
to create custom nodes.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ...core.models import NodeModel


class BaseNode(NodeModel, ABC):
    """
    Base class for creating custom nodes.

    Users should inherit from this class and implement the cook() method.

    Example::

        class AddNode(BaseNode):
            category = "Math"

            def __init__(self):
                super().__init__(name="Add", node_type="AddNode")

                # Define inputs
                self.add_input("a", data_type="float", default_value=0.0)
                self.add_input("b", data_type="float", default_value=0.0)

                # Define outputs
                self.add_output("result", data_type="float")

                # Define parameters
                self.add_parameter("multiplier", data_type="float", default_value=1.0)

            def cook(self, **inputs):
                a = inputs.get("a", 0.0)
                b = inputs.get("b", 0.0)
                multiplier = self.parameter("multiplier").value()

                result = (a + b) * multiplier
                return {"result": result}
    """

    # Class attributes that can be overridden
    category = "General"
    description = ""

    def __init__(
        self,
        name: str = "Node",
        node_type: str = "BaseNode",
        category: Optional[str] = None,
        **kwargs
    ):
        # Use class category if not provided
        if category is None:
            category = self.__class__.category

        super().__init__(
            name=name,
            node_type=node_type,
            category=category,
            **kwargs
        )

        # Call setup method for subclasses to define their interface
        self.setup()

    def setup(self) -> None:
        """
        Setup method called during initialization.

        Override this method to define inputs, outputs, and parameters.
        This is called AFTER __init__ to allow subclasses to customize.
        """
        pass

    def _cook_internal(self, **inputs) -> Dict[str, Any]:
        """
        Internal cook implementation that calls the user's compute method.

        This wraps the user's compute() method and handles common logic.
        """
        try:
            return self.compute(**inputs) or {}
        except Exception as e:
            print(f"Error in node {self.name}.compute(): {e}")
            raise

    @abstractmethod
    def compute(self, **inputs) -> Dict[str, Any]:
        """
        Compute method - implement your node's logic here.

        This method is called when the node needs to compute its outputs.
        It receives all input values as keyword arguments.

        Args:
            **inputs: Dictionary of input values (input_name -> value)

        Returns:
            Dictionary of output values (output_name -> value)

        Example::

            def compute(self, **inputs):
                a = inputs.get("a", 0.0)
                b = inputs.get("b", 0.0)
                result = a + b
                return {"result": result}
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
