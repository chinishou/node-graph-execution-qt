"""
Network Model
=============

Represents a node network (graph).
A network contains nodes and connections between them.
"""

from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID
import re

from .connector_model import ConnectorModel
from .node_model import NodeModel
from ..signals import Signal


class NetworkModel:
    """
    Data model for a node network.

    A network is a collection of nodes and connections between them.
    Similar to Houdini's network view.

    Attributes:
        name: Network name
        nodes: Dictionary of nodes (id -> NodeModel)
        connector_pairs: List of connections (tuples of connector pairs)
        node_added: Signal emitted when a node is added
        node_removed: Signal emitted when a node is removed
        connection_added: Signal emitted when a connection is added
        connection_removed: Signal emitted when a connection is removed
    """

    def __init__(self, name: str = "Network"):
        self.name = name
        self._nodes: Dict[UUID, NodeModel] = {}
        self._connector_pairs: List[Tuple[ConnectorModel, ConnectorModel]] = []

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

        node.name = self._get_unique_node_name(node.name)

        node.network = self
        self._nodes[node.id] = node

        self.node_added.emit(node)
        self.network_changed.emit()

        return True

    def _get_unique_node_name(self, base_name: str) -> str:
        """
        Generate a unique node name by adding suffix if needed.

        Args:
            base_name: The desired name for the node

        Returns:
            A unique name (original or with suffix like _1, _2, etc.)
        """
        existing_names = {node.name for node in self._nodes.values()}

        if base_name not in existing_names:
            return base_name

        match = re.match(r'^(.+?)_(\d+)$', base_name)
        if match:
            base_name = match.group(1)

        counter = 1
        while f"{base_name}_{counter}" in existing_names:
            counter += 1

        return f"{base_name}_{counter}"

    def remove_node(self, node_id: UUID) -> bool:
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

        # Remove connections from _connector_pairs that involve this node
        self._connector_pairs = [
            (src, tgt) for src, tgt in self._connector_pairs
            if src.node is not node and tgt.node is not node
        ]

        # Disconnect all connectors first
        for connector in list(node.inputs().values()) + list(node.outputs().values()):
            connector.disconnect_all()

        # Remove node
        del self._nodes[node_id]
        node.network = None

        self.node_removed.emit(node)
        self.network_changed.emit()

        return True

    def get_node(self, node_id: UUID) -> Optional[NodeModel]:
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
        source_node_id: UUID,
        source_output: str,
        target_node_id: UUID,
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
            True if connection was successful, False if it would create a cycle
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
            # Check if this connection creates a cycle
            if self.has_cycle():
                # Undo the connection
                source_connector.disconnect_from(target_connector)
                print(f"Warning: Connection from {source_node.name}.{source_output} to {target_node.name}.{target_input} would create a cycle")
                return False

            self._connector_pairs.append((source_connector, target_connector))

            self.connection_added.emit(source_connector, target_connector)
            self.network_changed.emit()

        return success

    def disconnect(
        self,
        source_node_id: UUID,
        source_output: str,
        target_node_id: UUID,
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
            # Remove from connector_pairs
            self._connector_pairs = [
                (src, tgt) for src, tgt in self._connector_pairs
                if not (src is source_connector and tgt is target_connector)
            ]

            self.connection_removed.emit(source_connector, target_connector)
            self.network_changed.emit()

        return success

    def connector_pairs(self) -> List[Tuple[ConnectorModel, ConnectorModel]]:
        """
        Get all connections in the network.

        Returns:
            List of (output_connector, input_connector) tuples
        """
        return self._connector_pairs.copy()

    # Execution

    def get_execution_order(self) -> List[NodeModel]:
        """
        Get nodes in topological execution order.

        Returns nodes sorted such that dependencies are cooked before dependents.
        Uses local topological sorting on terminal nodes and combines results.

        Returns:
            List of nodes in execution order
        """
        nodes = self.nodes()

        if not nodes:
            return []

        # Find terminal nodes (nodes with no downstream connections)
        terminal_nodes = []
        for node in nodes:
            has_downstream = any(
                output_conn.is_connected()
                for output_conn in node.outputs().values()
            )
            if not has_downstream:
                terminal_nodes.append(node)

        # If no terminal nodes found, use all nodes as potential terminals
        # (this handles isolated nodes or cycles)
        if not terminal_nodes:
            terminal_nodes = nodes

        # Process each terminal node using local topological sort
        processed = set()
        result = []

        for terminal in terminal_nodes:
            local_order = terminal._get_local_execution_order()
            for node in local_order:
                if node.id not in processed:
                    result.append(node)
                    processed.add(node.id)

        # Check if all nodes are processed
        if len(result) != len(nodes):
            unprocessed = [node.name for node in nodes if node.id not in processed]
            error_msg = (
                f"Cyclic dependency detected in network '{self.name}'. "
                f"Nodes in cycle: {', '.join(unprocessed)}. "
                f"Cannot determine execution order."
            )
            raise ValueError(error_msg)

        return result

    def mark_all_dirty(self) -> None:
        """Mark all nodes as dirty."""
        for node in self._nodes.values():
            node.mark_dirty()

    # Utility methods

    def clear(self) -> None:
        """Remove all nodes and connections."""
        self._connector_pairs.clear()
        node_ids = list(self._nodes.keys())
        for node_id in node_ids:
            self.remove_node(node_id)

    def find_parent_nodes(self, node: NodeModel) -> List[NodeModel]:
        """Find all parent nodes (nodes feeding into this node)."""
        parents = []

        for input_conn in node.inputs().values():
            for connected_output in input_conn.connections():
                if connected_output.node and connected_output.node not in parents:
                    parents.append(connected_output.node)

        return parents

    def find_child_nodes(self, node: NodeModel) -> List[NodeModel]:
        """Find all child nodes (nodes fed by this node)."""
        children = []

        for output_conn in node.outputs().values():
            for connected_input in output_conn.connections():
                if connected_input.node and connected_input.node not in children:
                    children.append(connected_input.node)

        return children

    def has_cycle(self) -> bool:
        """Check if the network contains any cycles."""
        visited = set()
        rec_stack = set()

        def visit(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            node = self._nodes[node_id]
            for child in self.find_child_nodes(node):
                if child.id not in visited:
                    if visit(child.id):
                        return True
                elif child.id in rec_stack:
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
                    "source_node": str(src.node.id) if src.node else None,
                    "source_output": src.name,
                    "target_node": str(tgt.node.id) if tgt.node else None,
                    "target_input": tgt.name,
                }
                for src, tgt in self.connector_pairs()
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
            # Convert string IDs back to UUID
            source_id = conn_data["source_node"]
            target_id = conn_data["target_node"]
            if isinstance(source_id, str):
                source_id = UUID(source_id)
            if isinstance(target_id, str):
                target_id = UUID(target_id)

            network.connect(
                source_node_id=source_id,
                source_output=conn_data["source_output"],
                target_node_id=target_id,
                target_input=conn_data["target_input"],
            )

        return network

    def __repr__(self) -> str:
        return f"NetworkModel(name='{self.name}', nodes={len(self._nodes)})"
