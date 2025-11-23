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
            # Set parent reference for path resolution
            self._internal_network._parent_node = self
            # Connect signals to auto-sync connectors
            self._internal_network.node_added.connect(self._on_internal_node_added)
            self._internal_network.node_removed.connect(self._on_internal_node_removed)

            # Auto-create default input and output nodes
            input_node = SubnetInputNode(connector_name="input1", data_type="any")
            input_node.set_position(100, 150)
            self._internal_network.add_node(input_node)

            output_node = SubnetOutputNode(connector_name="output1", data_type="any")
            output_node.set_position(400, 150)
            self._internal_network.add_node(output_node)

        # Parameters will be created dynamically based on I/O nodes

    def get_internal_network(self) -> NetworkModel:
        """Get the internal network."""
        if self._internal_network is None:
            self._internal_network = NetworkModel(name=f"{self.name}_network")
        return self._internal_network

    def set_internal_network(self, network: NetworkModel):
        """Set the internal network."""
        self._internal_network = network
        # Set parent reference for path resolution
        self._internal_network._parent_node = self
        # Connect signals to auto-sync connectors
        self._internal_network.node_added.connect(self._on_internal_node_added)
        self._internal_network.node_removed.connect(self._on_internal_node_removed)
        # Set parent subnet reference on all I/O nodes
        self._update_io_node_references()
        self._sync_connectors()

    def _update_io_node_references(self):
        """Update _parent_subnet reference on all I/O nodes in the internal network."""
        if not self._internal_network:
            return

        for node in self._internal_network.nodes():
            if isinstance(node, (SubnetInputNode, SubnetOutputNode)):
                # Set a private attribute to reference the parent subnet
                node._parent_subnet = self

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
                # Set parent subnet reference
                node._parent_subnet = self
                # Connect to parameter changes if not already connected
                if not node.parameter_changed.is_connected(self._on_io_node_parameter_changed):
                    node.parameter_changed.connect(self._on_io_node_parameter_changed)
            elif isinstance(node, SubnetOutputNode):
                output_nodes.append(node)
                # Set parent subnet reference
                node._parent_subnet = self
                # Connect to parameter changes if not already connected
                if not node.parameter_changed.is_connected(self._on_io_node_parameter_changed):
                    node.parameter_changed.connect(self._on_io_node_parameter_changed)

        # Create/update input connectors
        new_inputs = {}  # Maps connector_name to list of nodes with that name
        for input_node in input_nodes:
            connector_name = input_node.get_connector_name()
            if connector_name not in new_inputs:
                new_inputs[connector_name] = []
            new_inputs[connector_name].append(input_node)

        # Process each unique connector name
        for connector_name, nodes in new_inputs.items():
            data_type = nodes[0].get_data_type()

            # If there are multiple nodes with the same connector_name, rename duplicates
            if len(nodes) > 1:
                print(f"[SubnetNode] Found {len(nodes)} nodes with connector_name '{connector_name}', auto-renaming duplicates")
                for idx, node in enumerate(nodes):
                    if idx == 0:
                        # Keep the first one with original name
                        unique_name = connector_name
                    else:
                        # Auto-generate unique names for duplicates
                        base_name = connector_name.rstrip('0123456789')
                        counter = 2
                        while True:
                            unique_name = f"{base_name}{counter}"
                            # Check if this name is already used
                            if unique_name not in new_inputs and not self.input(unique_name):
                                break
                            counter += 1

                        # Update the node's parameter
                        print(f"[SubnetNode] Renaming duplicate input node from '{connector_name}' to '{unique_name}'")
                        node.parameter("connector_name").set_value(unique_name)
                        node.name = f"Input ({unique_name})"

                    # Add connector if it doesn't exist
                    if not self.input(unique_name):
                        self.add_input(unique_name, data_type=data_type)
            else:
                # Single node with this name
                if not self.input(connector_name):
                    self.add_input(connector_name, data_type=data_type)
                else:
                    # Update existing connector if needed
                    connector = self.input(connector_name)
                    if connector:
                        connector.data_type = data_type

        # Collect all active input connector names (including renamed ones)
        all_input_names = set()
        for connector_name, nodes in new_inputs.items():
            if len(nodes) > 1:
                # Include original and all renamed versions
                base_name = connector_name.rstrip('0123456789')
                for i in range(1, len(nodes) + 1):
                    if i == 1:
                        all_input_names.add(connector_name)
                    else:
                        all_input_names.add(f"{base_name}{i}")
            else:
                all_input_names.add(connector_name)

        # Remove old input connectors that no longer have corresponding nodes
        for input_name in existing_inputs:
            if input_name not in all_input_names:
                self.remove_input(input_name)

        # Create/update output connectors
        new_outputs = {}  # Maps connector_name to list of nodes with that name
        for output_node in output_nodes:
            connector_name = output_node.get_connector_name()
            if connector_name not in new_outputs:
                new_outputs[connector_name] = []
            new_outputs[connector_name].append(output_node)

        # Process each unique connector name
        for connector_name, nodes in new_outputs.items():
            data_type = nodes[0].get_data_type()

            # If there are multiple nodes with the same connector_name, rename duplicates
            if len(nodes) > 1:
                print(f"[SubnetNode] Found {len(nodes)} nodes with connector_name '{connector_name}', auto-renaming duplicates")
                for idx, node in enumerate(nodes):
                    if idx == 0:
                        # Keep the first one with original name
                        unique_name = connector_name
                    else:
                        # Auto-generate unique names for duplicates
                        base_name = connector_name.rstrip('0123456789')
                        counter = 2
                        while True:
                            unique_name = f"{base_name}{counter}"
                            # Check if this name is already used
                            if unique_name not in new_outputs and not self.output(unique_name):
                                break
                            counter += 1

                        # Update the node's parameter
                        print(f"[SubnetNode] Renaming duplicate output node from '{connector_name}' to '{unique_name}'")
                        node.parameter("connector_name").set_value(unique_name)
                        node.name = f"Output ({unique_name})"

                    # Add connector if it doesn't exist
                    if not self.output(unique_name):
                        self.add_output(unique_name, data_type=data_type)
            else:
                # Single node with this name
                if not self.output(connector_name):
                    self.add_output(connector_name, data_type=data_type)
                else:
                    # Update existing connector if needed
                    connector = self.output(connector_name)
                    if connector:
                        connector.data_type = data_type

        # Collect all active output connector names (including renamed ones)
        all_output_names = set()
        for connector_name, nodes in new_outputs.items():
            if len(nodes) > 1:
                # Include original and all renamed versions
                base_name = connector_name.rstrip('0123456789')
                for i in range(1, len(nodes) + 1):
                    if i == 1:
                        all_output_names.add(connector_name)
                    else:
                        all_output_names.add(f"{base_name}{i}")
            else:
                all_output_names.add(connector_name)

        # Remove old output connectors that no longer have corresponding nodes
        for output_name in existing_outputs:
            if output_name not in all_output_names:
                self.remove_output(output_name)

    def _on_internal_node_added(self, node):
        """Handle when a node is added to the internal network."""
        print(f"[SubnetNode] Node added to internal network: {node.name} (type: {type(node).__name__})")
        # If it's a subnet I/O node, sync connectors
        if isinstance(node, (SubnetInputNode, SubnetOutputNode)):
            print(f"[SubnetNode] Detected I/O node, syncing connectors for subnet: {self.name}")
            # Set parent subnet reference
            node._parent_subnet = self
            self._sync_connectors()
            # Also connect to parameter changes to re-sync when name/type changes
            node.parameter_changed.connect(self._on_io_node_parameter_changed)

    def _on_internal_node_removed(self, node):
        """Handle when a node is removed from the internal network."""
        # If it's a subnet I/O node, sync connectors
        if isinstance(node, (SubnetInputNode, SubnetOutputNode)):
            self._sync_connectors()

    def _on_io_node_parameter_changed(self):
        """Handle when a subnet I/O node's parameter changes."""
        # Re-sync connectors when connector name or data type changes
        self._sync_connectors()

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
            node.execute()

        # Step 3: Collect outputs from SubnetOutputNodes
        outputs = {}
        for node in self._internal_network.nodes():
            if isinstance(node, SubnetOutputNode):
                connector_name = node.get_connector_name()
                # Get the output value from the node's last outputs (stored by cook())
                if hasattr(node, '_last_outputs') and connector_name in node._last_outputs:
                    outputs[connector_name] = node._last_outputs[connector_name]

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

    def resolve_connector_display_type(
        self,
        connector_name: str,
        is_output: bool,
        visited: Optional[set] = None
    ) -> Optional[str]:
        """
        Resolve display type for subnet connectors by looking into internal network.

        For output connectors: look at the corresponding SubnetOutputNode's input type.
        """
        if not is_output or not self._internal_network:
            return None  # Use default resolution for inputs

        # For output connectors, check internal SubnetOutputNode
        from .subnet_io_nodes import SubnetOutputNode

        for node in self._internal_network.nodes():
            if isinstance(node, SubnetOutputNode):
                if node.get_connector_name() == connector_name:
                    # Get the input connector on SubnetOutputNode
                    internal_input = node.input(connector_name)
                    if internal_input and internal_input.is_connected():
                        # Get what's connected to it
                        connections = internal_input.connections()
                        if connections:
                            connected_connector = connections[0]
                            # Return concrete type if available
                            if connected_connector.data_type != 'any':
                                return connected_connector.data_type
                            # Otherwise, try to resolve from the connected node
                            if hasattr(connected_connector, 'node') and connected_connector.node:
                                connected_node = connected_connector.node
                                # Check for type parameters
                                for param_name in ['type', 'output_type', 'data_type', 'value_type']:
                                    param = connected_node.parameter(param_name)
                                    if param:
                                        param_value = param.value()
                                        # Basic type checking
                                        if param_value in ['int', 'float', 'str', 'bool']:
                                            return param_value
        return None

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
