"""
Subnet Node
===========

A node that contains an entire sub-network.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from pydantic import PrivateAttr
from ..base import BaseNode
from ...core.models import NetworkModel
from .subnet_io_nodes import SubnetInputNode, SubnetOutputNode


class SubnetNode(BaseNode):
    """
    A node that contains a sub-network.

    The subnet can have its own nodes and connections. Input/Output nodes
    within the subnet define the external interface.
    """

    category: str = "Network"
    description: str = "Container for a sub-network"

    # Private attributes
    _internal_network: Optional[NetworkModel] = PrivateAttr(default=None)

    def __init__(self, name: str = "Subnet", **kwargs):
        super().__init__(
            name=name,
            node_type="SubnetNode",
            **kwargs
        )

    def setup(self) -> None:
        """Setup the subnet node."""
        # Initialize internal network if not already set
        if self._internal_network is None:
            self._internal_network = NetworkModel(name=f"{self.name}_network")

        # Parameters will be created dynamically based on I/O nodes

    def get_internal_network(self) -> NetworkModel:
        """Get the internal network."""
        if self._internal_network is None:
            self._internal_network = NetworkModel(name=f"{self.name}_network")
        return self._internal_network

    def set_internal_network(self, network: NetworkModel):
        """Set the internal network."""
        self._internal_network = network
        self._sync_connectors()

    def _sync_connectors(self):
        """
        Synchronize external connectors with internal I/O nodes.

        Scans the internal network for SubnetInput/Output nodes and
        creates corresponding external connectors.
        """
        if not self._internal_network:
            return

        # Clear existing connectors (except built-in ones)
        # We need to be careful not to break existing connections
        existing_inputs = list(self.inputs().keys())
        existing_outputs = list(self.outputs().keys())

        # Find all subnet I/O nodes
        input_nodes = []
        output_nodes = []

        for node in self._internal_network.nodes():
            if isinstance(node, SubnetInputNode):
                input_nodes.append(node)
            elif isinstance(node, SubnetOutputNode):
                output_nodes.append(node)

        # Create/update input connectors
        new_inputs = set()
        for input_node in input_nodes:
            connector_name = input_node.get_connector_name()
            data_type = input_node.get_data_type()
            new_inputs.add(connector_name)

            # Add or update connector
            if connector_name not in existing_inputs:
                self.add_input(connector_name, data_type=data_type)
            else:
                # Update existing connector if needed
                connector = self.input(connector_name)
                if connector:
                    connector.data_type = data_type

        # Remove old input connectors that no longer have corresponding nodes
        for input_name in existing_inputs:
            if input_name not in new_inputs:
                self.remove_input(input_name)

        # Create/update output connectors
        new_outputs = set()
        for output_node in output_nodes:
            connector_name = output_node.get_connector_name()
            data_type = output_node.get_data_type()
            new_outputs.add(connector_name)

            # Add or update connector
            if connector_name not in existing_outputs:
                self.add_output(connector_name, data_type=data_type)
            else:
                # Update existing connector if needed
                connector = self.output(connector_name)
                if connector:
                    connector.data_type = data_type

        # Remove old output connectors that no longer have corresponding nodes
        for output_name in existing_outputs:
            if output_name not in new_outputs:
                self.remove_output(output_name)

    def compute(self, **inputs) -> Dict[str, Any]:
        """
        Execute the internal network.

        Steps:
        1. Inject input values into SubnetInputNodes
        2. Execute the internal network
        3. Collect output values from SubnetOutputNodes
        """
        if not self._internal_network:
            return {}

        # Step 1: Inject inputs into SubnetInputNodes
        for node in self._internal_network.nodes():
            if isinstance(node, SubnetInputNode):
                connector_name = node.get_connector_name()
                if connector_name in inputs:
                    # Store the input value in the node for later retrieval
                    node._injected_input = inputs[connector_name]

        # Step 2: Execute the internal network
        # Get execution order
        execution_order = self._internal_network.get_execution_order()

        # Execute nodes in order
        for node in execution_order:
            if isinstance(node, SubnetInputNode):
                # For input nodes, use the injected value
                if hasattr(node, '_injected_input'):
                    connector_name = node.get_connector_name()
                    node._cached_outputs = {connector_name: node._injected_input}
                else:
                    node.execute()
            else:
                node.execute()

        # Step 3: Collect outputs from SubnetOutputNodes
        outputs = {}
        for node in self._internal_network.nodes():
            if isinstance(node, SubnetOutputNode):
                connector_name = node.get_connector_name()
                # Get the output value from the node's cached outputs
                if hasattr(node, '_cached_outputs') and connector_name in node._cached_outputs:
                    outputs[connector_name] = node._cached_outputs[connector_name]

        return outputs

    def add_subnet_input(self, name: str, data_type: str = "any") -> SubnetInputNode:
        """
        Add a new input to the subnet.

        Creates a SubnetInputNode in the internal network.
        """
        network = self.get_internal_network()

        # Create the input node
        input_node = SubnetInputNode(connector_name=name, data_type=data_type)
        network.add_node(input_node)

        # Sync connectors
        self._sync_connectors()

        return input_node

    def add_subnet_output(self, name: str, data_type: str = "any") -> SubnetOutputNode:
        """
        Add a new output to the subnet.

        Creates a SubnetOutputNode in the internal network.
        """
        network = self.get_internal_network()

        # Create the output node
        output_node = SubnetOutputNode(connector_name=name, data_type=data_type)
        network.add_node(output_node)

        # Sync connectors
        self._sync_connectors()

        return output_node

    def serialize(self) -> Dict[str, Any]:
        """Serialize the subnet node including its internal network."""
        data = super().serialize()

        # Add internal network
        if self._internal_network:
            data["internal_network"] = self._internal_network.serialize()

        return data

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "SubnetNode":
        """Deserialize a subnet node."""
        # Create the subnet node
        node = cls(name=data.get("name", "Subnet"))

        # Deserialize internal network if present
        if "internal_network" in data:
            from ...core.models import NetworkModel
            network = NetworkModel.deserialize(data["internal_network"])
            node.set_internal_network(network)

        return node
