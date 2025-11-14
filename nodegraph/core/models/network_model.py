"""
Network Model
=============

Represents a node network (graph).
A network contains nodes and connections between them.
"""

from typing import Dict, List, Optional, Tuple, Any
from uuid import uuid4
from .node_model import NodeModel
from .connector_model import ConnectorModel
from ..signals import Signal


class NetworkModel:
    """
    Data model for a node network.

    A network is a collection of nodes and connections between them.
    Similar to Houdini's network view.

    Attributes:
        name: Network name
        nodes: Dictionary of nodes (id -> NodeModel)
        connections: List of connections (tuples of connector pairs)
        node_added: Signal emitted when a node is added
        node_removed: Signal emitted when a node is removed
        connection_added: Signal emitted when a connection is added
        connection_removed: Signal emitted when a connection is removed
    """

    def __init__(self, name: str = "Network"):
        self.name = name
        self._nodes: Dict[str, NodeModel] = {}

        # Signals
        self.node_added = Signal()
        self.node_removed = Signal()
        self.connection_added = Signal()
        self.connection_removed = Signal()
        self.network_changed = Signal()

    # Node management

    def add_node(self, node: NodeModel) -> bool:
        """
        Add a node to the network.

        Args:
            node: The node to add

        Returns:
            True if node was added successfully
        """
        if node.id in self._nodes:
            return False

        node.network = self
        self._nodes[node.id] = node

        self.node_added.emit(node)
        self.network_changed.emit()

        return True

    def remove_node(self, node_id: str) -> bool:
        """
        Remove a node from the network.

        Args:
            node_id: ID of the node to remove

        Returns:
            True if node was removed successfully
        """
        node = self._nodes.get(node_id)
        if not node:
            return False

        # Disconnect all connectors first
        for connector in list(node.inputs().values()) + list(node.outputs().values()):
            connector.disconnect_all()

        # Remove node
        del self._nodes[node_id]
        node.network = None

        self.node_removed.emit(node)
        self.network_changed.emit()

        return True

    def get_node(self, node_id: str) -> Optional[NodeModel]:
        """Get node by ID."""
        return self._nodes.get(node_id)

    def get_node_by_name(self, name: str) -> Optional[NodeModel]:
        """Get node by name (returns first match)."""
        for node in self._nodes.values():
            if node.name == name:
                return node
        return None

    def nodes(self) -> List[NodeModel]:
        """Get all nodes in the network."""
        return list(self._nodes.values())

    def node_count(self) -> int:
        """Get the number of nodes in the network."""
        return len(self._nodes)

    # Connection management

    def connect(
        self,
        source_node_id: str,
        source_output: str,
        target_node_id: str,
        target_input: str
    ) -> bool:
        """
        Create a connection between two nodes.

        Args:
            source_node_id: ID of the source node
            source_output: Name of the output connector
            target_node_id: ID of the target node
            target_input: Name of the input connector

        Returns:
            True if connection was successful
        """
        source_node = self.get_node(source_node_id)
        target_node = self.get_node(target_node_id)

        if not source_node or not target_node:
            return False

        source_connector = source_node.output(source_output)
        target_connector = target_node.input(target_input)

        if not source_connector or not target_connector:
            return False

        success = source_connector.connect_to(target_connector)

        if success:
            self.connection_added.emit(source_connector, target_connector)
            self.network_changed.emit()

        return success

    def disconnect(
        self,
        source_node_id: str,
        source_output: str,
        target_node_id: str,
        target_input: str
    ) -> bool:
        """
        Remove a connection between two nodes.

        Args:
            source_node_id: ID of the source node
            source_output: Name of the output connector
            target_node_id: ID of the target node
            target_input: Name of the input connector

        Returns:
            True if disconnection was successful
        """
        source_node = self.get_node(source_node_id)
        target_node = self.get_node(target_node_id)

        if not source_node or not target_node:
            return False

        source_connector = source_node.output(source_output)
        target_connector = target_node.input(target_input)

        if not source_connector or not target_connector:
            return False

        success = source_connector.disconnect_from(target_connector)

        if success:
            self.connection_removed.emit(source_connector, target_connector)
            self.network_changed.emit()

        return success

    def connections(self) -> List[Tuple[ConnectorModel, ConnectorModel]]:
        """
        Get all connections in the network.

        Returns:
            List of (output_connector, input_connector) tuples
        """
        conns = []

        for node in self._nodes.values():
            for output in node.outputs().values():
                for connected_input in output.connections():
                    if connected_input.is_input():
                        conns.append((output, connected_input))

        return conns

    # Execution

    def cook_all(self) -> None:
        """
        Cook all dirty nodes in the network in topological order.

        This ensures that nodes are cooked in the correct dependency order,
        avoiding redundant computation.
        """
        sorted_nodes = self.get_execution_order()
        for node in sorted_nodes:
            if node.is_dirty():
                node.cook()

    def get_execution_order(self) -> List[NodeModel]:
        """
        Get nodes in topological execution order using Kahn's algorithm.

        Returns nodes sorted such that dependencies are cooked before dependents.
        Nodes with no dependencies come first.

        Returns:
            List of nodes in execution order
        """
        nodes = self.nodes()

        if not nodes:
            return []

        # Build node ID to node mapping (since nodes are not hashable)
        node_map = {node.id: node for node in nodes}

        # Build adjacency list and in-degree count using node IDs
        in_degree = {node.id: 0 for node in nodes}
        adjacency = {node.id: [] for node in nodes}

        for node in nodes:
            for output_conn in node.outputs().values():
                for connected_input in output_conn.connections():
                    if connected_input.node:
                        target_node = connected_input.node
                        adjacency[node.id].append(target_node.id)
                        in_degree[target_node.id] += 1

        # Queue of node IDs with no dependencies
        queue = [node.id for node in nodes if in_degree[node.id] == 0]
        sorted_nodes = []

        while queue:
            node_id = queue.pop(0)
            sorted_nodes.append(node_map[node_id])

            # Reduce in-degree for downstream nodes
            for neighbor_id in adjacency[node_id]:
                in_degree[neighbor_id] -= 1
                if in_degree[neighbor_id] == 0:
                    queue.append(neighbor_id)

        # Check for cycles
        if len(sorted_nodes) != len(nodes):
            print("Warning: Cyclic graph detected, some nodes may not be included in execution order")

        return sorted_nodes

    def mark_all_dirty(self) -> None:
        """Mark all nodes as dirty."""
        for node in self._nodes.values():
            node.mark_dirty()

    # Utility methods

    def clear(self) -> None:
        """Remove all nodes and connections."""
        node_ids = list(self._nodes.keys())
        for node_id in node_ids:
            self.remove_node(node_id)

    def find_upstream_nodes(self, node: NodeModel) -> List[NodeModel]:
        """Find all nodes upstream (feeding into) a given node."""
        upstream = []

        for input_conn in node.inputs().values():
            for connected_output in input_conn.connections():
                if connected_output.node and connected_output.node not in upstream:
                    upstream.append(connected_output.node)

        return upstream

    def find_downstream_nodes(self, node: NodeModel) -> List[NodeModel]:
        """Find all nodes downstream (fed by) a given node."""
        downstream = []

        for output_conn in node.outputs().values():
            for connected_input in output_conn.connections():
                if connected_input.node and connected_input.node not in downstream:
                    downstream.append(connected_input.node)

        return downstream

    def has_cycle(self) -> bool:
        """Check if the network contains any cycles."""
        visited = set()
        rec_stack = set()

        def visit(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            node = self._nodes[node_id]
            for downstream in self.find_downstream_nodes(node):
                if downstream.id not in visited:
                    if visit(downstream.id):
                        return True
                elif downstream.id in rec_stack:
                    return True

            rec_stack.remove(node_id)
            return False

        for node_id in self._nodes:
            if node_id not in visited:
                if visit(node_id):
                    return True

        return False

    # Serialization

    def serialize(self) -> Dict[str, Any]:
        """Serialize network to dictionary."""
        return {
            "name": self.name,
            "nodes": [
                node.serialize() for node in self._nodes.values()
            ],
            "connections": [
                {
                    "source_node": src.node.id if src.node else None,
                    "source_output": src.name,
                    "target_node": tgt.node.id if tgt.node else None,
                    "target_input": tgt.name,
                }
                for src, tgt in self.connections()
            ],
        }

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "NetworkModel":
        """Deserialize network from dictionary."""
        network = cls(name=data.get("name", "Network"))

        # First, create all nodes
        node_map = {}
        for node_data in data.get("nodes", []):
            node = NodeModel.deserialize(node_data, network)
            network.add_node(node)
            node_map[node.id] = node

        # Then, recreate connections
        for conn_data in data.get("connections", []):
            network.connect(
                source_node_id=conn_data["source_node"],
                source_output=conn_data["source_output"],
                target_node_id=conn_data["target_node"],
                target_input=conn_data["target_input"],
            )

        return network

    def __repr__(self) -> str:
        return f"NetworkModel(name='{self.name}', nodes={len(self._nodes)})"
