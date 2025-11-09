"""
Subnet Node
===========

A node that contains a sub-network of other nodes.
Similar to Houdini's Subnet or Blender's Node Group.
"""

from typing import Dict, Any, Optional
from .base_node import BaseNode
from ...core.models import NetworkModel


class SubnetNode(BaseNode):
    """
    A node that encapsulates a sub-network.

    Subnet nodes allow you to group multiple nodes together and
    treat them as a single node. This is useful for:
    - Organizing complex networks
    - Creating reusable components
    - Hiding implementation details

    The subnet has an internal network with special input/output nodes
    that connect to the subnet node's external interface.
    """

    category = "Network"
    description = "Container for a sub-network of nodes"

    def __init__(self, name: str = "Subnet", **kwargs):
        # Create internal network
        self._internal_network: Optional[NetworkModel] = NetworkModel(name=f"{name}_internal")

        super().__init__(name=name, node_type="SubnetNode", **kwargs)

    def setup(self) -> None:
        """Setup subnet node with default interface."""
        # Subnets start with no inputs/outputs
        # Users can add them dynamically
        pass

    def internal_network(self) -> NetworkModel:
        """Get the internal network of this subnet."""
        return self._internal_network

    def add_subnet_input(self, name: str, data_type: str = "any", default_value: Any = None):
        """
        Add an input to the subnet.

        This creates both:
        - An external input connector on the subnet node
        - An internal output node that provides this input to the subnet
        """
        # Add external input
        self.add_input(name, data_type=data_type, default_value=default_value)

        # TODO: Create internal input node in the subnet network
        # This would be a special node that outputs the external input value

    def add_subnet_output(self, name: str, data_type: str = "any"):
        """
        Add an output to the subnet.

        This creates both:
        - An external output connector on the subnet node
        - An internal input node that receives values from the subnet
        """
        # Add external output
        self.add_output(name, data_type=data_type)

        # TODO: Create internal output node in the subnet network
        # This would be a special node that captures values to output

    def compute(self, **inputs) -> Dict[str, Any]:
        """
        Cook the subnet by evaluating its internal network.

        The subnet's inputs are fed into the internal network,
        and the internal network's outputs are returned.
        """
        # TODO: Implement subnet cooking
        # 1. Pass inputs to internal input nodes
        # 2. Cook the internal network
        # 3. Collect outputs from internal output nodes
        # 4. Return collected outputs

        # For now, return empty dict (placeholder)
        return {}

    def serialize(self) -> Dict[str, Any]:
        """Serialize subnet including internal network."""
        data = super().serialize()

        # Add internal network data
        data["internal_network"] = self._internal_network.serialize() if self._internal_network else None

        return data

    @classmethod
    def deserialize(cls, data: Dict[str, Any], network: Optional[NetworkModel] = None) -> "SubnetNode":
        """Deserialize subnet including internal network."""
        # Create subnet node
        subnet = cls(name=data.get("name", "Subnet"))

        # Deserialize internal network if present
        if "internal_network" in data and data["internal_network"]:
            subnet._internal_network = NetworkModel.deserialize(data["internal_network"])

        # TODO: Properly deserialize all subnet properties

        return subnet

    def collapse(self) -> None:
        """Collapse subnet (hide internal network in UI)."""
        # This is a UI concern, not model concern
        # Could emit a signal here for the view to handle
        pass

    def expand(self) -> None:
        """Expand subnet (show internal network in UI)."""
        # This is a UI concern, not model concern
        pass
