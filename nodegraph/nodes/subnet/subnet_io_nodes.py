"""
Subnet I/O Nodes
=================

Special nodes that act as input/output interfaces for subnets.
"""

from typing import Dict, Any, Optional
from pydantic import PrivateAttr
from ..base import BaseNode


class SubnetInputNode(BaseNode):
    """
    Special node that represents an input to a subnet.

    Each SubnetInputNode creates a corresponding input connector
    on the parent SubnetNode.
    """

    category: str = "Subnet"
    description: str = "Input connector for subnet"

    # Private attributes
    _setup_connector_name: str = PrivateAttr(default="input")
    _setup_data_type: str = PrivateAttr(default="any")
    _setup_default_value: Any = PrivateAttr(default=None)

    def __init__(self, connector_name: str = "input", data_type: str = "any",
                 default_value: Any = None, **kwargs):
        # Pass setup parameters through kwargs for BaseNode to handle
        kwargs['_setup_connector_name'] = connector_name
        kwargs['_setup_data_type'] = data_type
        kwargs['_setup_default_value'] = default_value

        super().__init__(
            name=f"Input ({connector_name})",
            node_type="SubnetInputNode",
            **kwargs
        )

    def setup(self) -> None:
        """Setup the subnet input node."""
        # Add output that will pass through the input value
        self.add_output(
            self._setup_connector_name,
            data_type=self._setup_data_type,
            label=self._setup_connector_name
        )

        # Add parameter to configure the connector
        self.add_parameter("connector_name", data_type="string",
                         default_value=self._setup_connector_name,
                         label="Connector Name")
        self.add_parameter("data_type", data_type="string",
                         default_value=self._setup_data_type,
                         label="Data Type")

    def compute(self, **inputs) -> Dict[str, Any]:
        """
        Pass through the input value from the parent subnet node.

        The actual value is injected by the subnet execution system.
        """
        connector_name = self.parameter("connector_name").value()

        # Check if there's an injected input value (from subnet execution)
        if hasattr(self, '_injected_input'):
            return {connector_name: self._injected_input}

        # Try to get value from parent subnet (for direct execution in UI)
        if hasattr(self, '_parent_subnet') and self._parent_subnet:
            parent_input = self._parent_subnet.input(connector_name)
            if parent_input:
                value = parent_input.get_value()
                return {connector_name: value}

        # Otherwise, return the default value
        return {connector_name: self._setup_default_value}

    def get_connector_name(self) -> str:
        """Get the connector name."""
        return self.parameter("connector_name").value()

    def get_data_type(self) -> str:
        """Get the data type."""
        return self.parameter("data_type").value()

    def resolve_connector_display_type(
        self,
        connector_name: str,
        is_output: bool,
        visited: Optional[set] = None
    ) -> Optional[str]:
        """
        Resolve display type for SubnetInputNode output by checking parent subnet's input.

        For output connectors: look at what's connected to the parent SubnetNode's input.
        Recursively resolves through SubnetNode chains.
        """
        if not is_output:
            return None  # Use default resolution for inputs

        # Check if we have a parent subnet reference
        if not hasattr(self, '_parent_subnet') or not self._parent_subnet:
            return None

        parent_subnet = self._parent_subnet
        external_input = parent_subnet.input(connector_name)

        if external_input and external_input.is_connected():
            # Get what's connected to the external input
            connections = external_input.connections()
            if connections:
                connected_connector = connections[0]

                # Prevent infinite recursion
                if visited is None:
                    visited = set()
                connector_id = id(connected_connector)
                if connector_id in visited:
                    return None
                visited.add(connector_id)

                # Return concrete type if available
                if connected_connector.data_type != 'any':
                    return connected_connector.data_type

                # Try to resolve from connected node
                if hasattr(connected_connector, 'node') and connected_connector.node:
                    connected_node = connected_connector.node

                    # Recursively resolve if connected node supports it (e.g., SubnetNode chains)
                    if hasattr(connected_node, 'resolve_connector_display_type'):
                        custom_type = connected_node.resolve_connector_display_type(
                            connected_connector.name,
                            True,  # is_output
                            visited
                        )
                        if custom_type:
                            return custom_type

                    # Fallback to parameter checking
                    for param_name in ['type', 'output_type', 'data_type', 'value_type']:
                        param = connected_node.parameter(param_name)
                        if param:
                            param_value = param.value()
                            if param_value in ['int', 'float', 'str', 'bool']:
                                return param_value

        return None


class SubnetOutputNode(BaseNode):
    """
    Special node that represents an output from a subnet.

    Each SubnetOutputNode creates a corresponding output connector
    on the parent SubnetNode.
    """

    category: str = "Subnet"
    description: str = "Output connector for subnet"

    # Private attributes
    _setup_connector_name: str = PrivateAttr(default="output")
    _setup_data_type: str = PrivateAttr(default="any")

    def __init__(self, connector_name: str = "output", data_type: str = "any", **kwargs):
        # Pass setup parameters through kwargs for BaseNode to handle
        kwargs['_setup_connector_name'] = connector_name
        kwargs['_setup_data_type'] = data_type

        super().__init__(
            name=f"Output ({connector_name})",
            node_type="SubnetOutputNode",
            **kwargs
        )

    def setup(self) -> None:
        """Setup the subnet output node."""
        # Add input that receives the value to output
        self.add_input(
            self._setup_connector_name,
            data_type=self._setup_data_type,
            label=self._setup_connector_name
        )

        # Add parameter to configure the connector
        self.add_parameter("connector_name", data_type="string",
                         default_value=self._setup_connector_name,
                         label="Connector Name")
        self.add_parameter("data_type", data_type="string",
                         default_value=self._setup_data_type,
                         label="Data Type")

    def compute(self, **inputs) -> Dict[str, Any]:
        """
        Receive the output value and pass it to the parent subnet node.

        The subnet execution system will collect this value.
        """
        connector_name = self.parameter("connector_name").value()
        value = inputs.get(connector_name)

        # Return the value for the subnet execution system to collect
        return {connector_name: value}

    def get_connector_name(self) -> str:
        """Get the connector name."""
        return self.parameter("connector_name").value()

    def get_data_type(self) -> str:
        """Get the data type."""
        return self.parameter("data_type").value()
