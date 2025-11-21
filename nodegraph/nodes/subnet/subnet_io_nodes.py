"""
Subnet I/O Nodes
=================

Special nodes that act as input/output interfaces for subnets.
"""

from typing import Dict, Any, Optional
from ..base import BaseNode


class SubnetInputNode(BaseNode):
    """
    Special node that represents an input to a subnet.

    Each SubnetInputNode creates a corresponding input connector
    on the parent SubnetNode.
    """

    category: str = "Subnet"
    description: str = "Input connector for subnet"

    def __init__(self, connector_name: str = "input", data_type: str = "any",
                 default_value: Any = None, **kwargs):
        # Store setup parameters
        self._setup_connector_name = connector_name
        self._setup_data_type = data_type
        self._setup_default_value = default_value

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
        # This will be overridden during subnet execution
        # The subnet node will inject the actual input value
        connector_name = self.parameter("connector_name").value()
        return {connector_name: self._setup_default_value}

    def get_connector_name(self) -> str:
        """Get the connector name."""
        return self.parameter("connector_name").value()

    def get_data_type(self) -> str:
        """Get the data type."""
        return self.parameter("data_type").value()


class SubnetOutputNode(BaseNode):
    """
    Special node that represents an output from a subnet.

    Each SubnetOutputNode creates a corresponding output connector
    on the parent SubnetNode.
    """

    category: str = "Subnet"
    description: str = "Output connector for subnet"

    def __init__(self, connector_name: str = "output", data_type: str = "any", **kwargs):
        # Store setup parameters
        self._setup_connector_name = connector_name
        self._setup_data_type = data_type

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
