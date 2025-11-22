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

    # Class attributes that can be overridden (must have type annotations for Pydantic)
    category: str = "General"
    description: str = ""

    def __init__(
        self,
        name: str = "Node",
        node_type: str = "BaseNode",
        category: Optional[str] = None,
        **kwargs
    ):
        # Use class category default if not provided
        if category is None:
            # For Pydantic models, get the default from model_fields
            category_field = self.__class__.model_fields.get('category')
            if category_field and category_field.default is not None:
                category = category_field.default
            else:
                category = "General"

        # Extract setup parameters from kwargs (used by VariableNode)
        setup_params = {}
        for key in list(kwargs.keys()):
            if key.startswith('_setup_'):
                setup_params[key] = kwargs.pop(key)

        super().__init__(
            name=name,
            node_type=node_type,
            category=category,
            **kwargs
        )

        # Store setup parameters as instance attributes
        for key, value in setup_params.items():
            object.__setattr__(self, key, value)

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

    def resolve_connector_display_type(
        self,
        connector_name: str,
        is_output: bool,
        visited: Optional[set] = None
    ) -> Optional[str]:
        """
        Resolve the display type for a connector (for UI color coding).

        This method can be overridden by subclasses to provide custom type
        resolution logic for special cases (e.g., cross-network-boundary
        scenarios, type-transforming nodes).

        Args:
            connector_name: Name of the connector
            is_output: True if output connector, False if input connector
            visited: Set of already visited connector IDs (to prevent loops)

        Returns:
            Resolved type string (e.g., 'int', 'float', 'str'),
            or None to use default resolution logic

        Example::

            # In a SubnetNode subclass:
            def resolve_connector_display_type(self, connector_name, is_output, visited):
                if is_output:
                    # Look inside internal network for type
                    return self._resolve_internal_output_type(connector_name)
                return None  # Use default for inputs
        """
        return None  # Default: use standard resolution

    def transforms_data_type(self) -> bool:
        """
        Indicate whether this node transforms data types.

        Override this to return True for nodes that convert between types
        (e.g., ConvertNode). This affects how the UI resolves connector colors.

        Returns:
            True if node transforms types, False otherwise
        """
        return False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
