"""
Node Model
==========

Represents a node in the network graph.
Nodes are the fundamental building blocks that process data.
"""

from pydantic import BaseModel, Field, PrivateAttr
from typing import Dict, Any, Optional, TYPE_CHECKING, Tuple, List
from uuid import uuid4, UUID
from collections import defaultdict, deque

from .connector_model import ConnectorModel, ConnectorType
from .parameter_model import ParameterModel
from ..signals import Signal

if TYPE_CHECKING:
    from .network_model import NetworkModel


class NodeModel(BaseModel):
    """
    Data model for a node.

    Nodes are the processing units in a network. They have inputs, outputs,
    and parameters that control their behavior. Similar to Houdini's nodes.

    Attributes:
        id: Unique node identifier (UUID)
        name: Node display name
        node_type: Type of node (e.g., "AddNode", "SubnetNode")
        category: Category for organization (e.g., "Math", "Logic")
        network: The network this node belongs to
        color: Optional custom color
        parameters: Dictionary of parameters
        inputs: Dictionary of input connectors
        outputs: Dictionary of output connectors
        dirty_changed: Signal emitted when dirty state changes
        position_changed: Signal emitted when position changes
    """

    id: UUID = Field(default_factory=uuid4)
    name: str = "Node"
    node_type: str = "BaseNode"
    category: str = "General"
    network: Optional["NetworkModel"] = Field(default=None, exclude=True)
    color: Optional[str] = None
    enable_caching: bool = False

    # Private attributes
    _position: Tuple[float, float] = PrivateAttr(default=(0.0, 0.0))
    _parameters: Dict[str, ParameterModel] = PrivateAttr(default_factory=dict)
    _inputs: Dict[str, ConnectorModel] = PrivateAttr(default_factory=dict)
    _outputs: Dict[str, ConnectorModel] = PrivateAttr(default_factory=dict)
    _is_dirty: bool = PrivateAttr(default=True)
    _is_cooking: bool = PrivateAttr(default=False)
    _cached_outputs: Dict[str, Any] = PrivateAttr(default_factory=dict)
    _cook_error: Optional[str] = PrivateAttr(default=None)
    _dirty_changed: Signal = PrivateAttr(default=None)
    _position_changed: Signal = PrivateAttr(default=None)
    _parameter_changed: Signal = PrivateAttr(default=None)

    model_config = {
        "arbitrary_types_allowed": True,  # Allow Signal and custom types
    }

    def model_post_init(self, __context) -> None:
        """Initialize fields after Pydantic validation."""
        self._dirty_changed = Signal()
        self._position_changed = Signal()
        self._parameter_changed = Signal()

    @property
    def dirty_changed(self) -> Signal:
        """Get dirty_changed signal."""
        return self._dirty_changed

    @property
    def position_changed(self) -> Signal:
        """Get position_changed signal."""
        return self._position_changed

    @property
    def parameter_changed(self) -> Signal:
        """Get parameter_changed signal."""
        return self._parameter_changed

    def position(self) -> Tuple[float, float]:
        """Get node position."""
        return self._position

    def set_position(self, x: float, y: float, emit_signal: bool = True) -> None:
        """Set node position."""
        old_pos = self._position
        self._position = (x, y)

        if emit_signal and old_pos != self._position:
            self._position_changed.emit(x, y)

    # Parameter management

    def add_parameter(
        self,
        name: str,
        data_type: str = "float",
        default_value: Any = None,
        **kwargs
    ) -> ParameterModel:
        """Add a parameter to this node."""
        param = ParameterModel(
            name=name,
            data_type=data_type,
            default_value=default_value,
            **kwargs
        )
        self._parameters[name] = param

        # Connect parameter value changes to mark node dirty
        param.value_changed.connect(self._on_parameter_changed)

        return param

    def parameter(self, name: str) -> Optional[ParameterModel]:
        """Get parameter by name."""
        return self._parameters.get(name)

    def parameters(self) -> Dict[str, ParameterModel]:
        """Get all parameters."""
        return self._parameters.copy()

    def _on_parameter_changed(self, value: Any) -> None:
        """Handle parameter value changes."""
        self.mark_dirty()
        self._parameter_changed.emit()

    # Connector management

    def add_input(
        self,
        name: str,
        data_type: str = "any",
        default_value: Any = None,
        **kwargs
    ) -> ConnectorModel:
        """Add an input connector to this node."""
        connector = ConnectorModel(
            name=name,
            connector_type=ConnectorType.INPUT,
            data_type=data_type,
            node=self,
            default_value=default_value,
            **kwargs
        )
        self._inputs[name] = connector

        # Connect to mark node dirty when connection changes
        connector.connected_changed.connect(self.mark_dirty)

        return connector

    def add_output(
        self,
        name: str,
        data_type: str = "any",
        **kwargs
    ) -> ConnectorModel:
        """Add an output connector to this node."""
        connector = ConnectorModel(
            name=name,
            connector_type=ConnectorType.OUTPUT,
            data_type=data_type,
            node=self,
            **kwargs
        )
        self._outputs[name] = connector

        return connector

    def input(self, name: str) -> Optional[ConnectorModel]:
        """Get input connector by name."""
        return self._inputs.get(name)

    def output(self, name: str) -> Optional[ConnectorModel]:
        """Get output connector by name."""
        return self._outputs.get(name)

    def inputs(self) -> Dict[str, ConnectorModel]:
        """Get all input connectors."""
        return self._inputs.copy()

    def outputs(self) -> Dict[str, ConnectorModel]:
        """Get all output connectors."""
        return self._outputs.copy()

    def get_parent_nodes(self) -> list:
        """Get all parent nodes (nodes feeding into this node)."""
        if self.network is None:
            return []
        return self.network.find_parent_nodes(self)

    def get_child_nodes(self) -> list:
        """Get all child nodes (nodes fed by this node)."""
        if self.network is None:
            return []
        return self.network.find_child_nodes(self)

    # Execution (cooking)

    def mark_dirty(self) -> None:
        """Mark this node as dirty (needs recomputation)."""
        if not self.enable_caching:
            return  # Skip dirty state tracking when caching is disabled

        if not self._is_dirty:
            self._is_dirty = True
            self._cached_outputs.clear()
            self._cook_error = None

            # Propagate dirty state to outputs
            for output in self._outputs.values():
                output.mark_dirty()

            self._dirty_changed.emit(True)

    def is_dirty(self) -> bool:
        """Check if node needs recomputation."""
        if not self.enable_caching:
            return True  # Always dirty when caching is disabled
        return self._is_dirty

    def cook(self) -> bool:
        """
        Execute this node.

        Returns:
            True if cooking was successful, False if error occurred
        """
        # Skip cache check if caching is disabled (always recompute)
        if self.enable_caching:
            if not self._is_dirty and self._cached_outputs:
                return True  # Already up-to-date

        if self._is_cooking:
            return False  # Prevent recursion

        self._is_cooking = True
        self._cook_error = None

        try:
            # Gather input values
            input_values = {}
            for name, connector in self._inputs.items():
                input_values[name] = connector.get_value()

            output_values = self._cook_internal(**input_values)

            # Store outputs (even if empty dict)
            if output_values is not None:
                self._cached_outputs = output_values
            else:
                self._cached_outputs = {}

            # Mark as clean (only if caching is enabled)
            if self.enable_caching:
                self._is_dirty = False
                self._dirty_changed.emit(False)

            return True

        except Exception as e:
            self._cook_error = str(e)
            print(f"Error cooking node {self.name}: {e}")
            return False

        finally:
            self._is_cooking = False

    def _cook_internal(self, **inputs) -> Dict[str, Any]:
        """
        Internal cook method to be overridden by subclasses.

        Args:
            **inputs: Dictionary of input values

        Returns:
            Dictionary of output values
        """
        # Base implementation does nothing
        return {}

    def execute(self) -> bool:
        """
        Execute this node by cooking all parent nodes first, then cooking this node.

        This ensures all dependencies are up-to-date before cooking this node.
        Uses local topological sorting on ancestors only.

        Returns:
            True if execution was successful, False if error occurred
        """
        if self.network is None:
            return self.cook()

        # Get local execution order (ancestors + self)
        try:
            nodes_to_cook = self._get_local_execution_order()
        except ValueError as e:
            print(f"Error: Cannot execute node {self.name}: {e}")
            return False

        # Cook nodes in order
        for node in nodes_to_cook:
            if not self.enable_caching or node.is_dirty():
                if not node.cook():
                    return False

        return True

    def _get_all_ancestors(self) -> List["NodeModel"]:
        """
        Get all ancestor nodes (recursive parent traversal).

        Returns:
            List of all ancestor nodes
        """
        ancestors = []
        visited = set()
        to_visit = list(self.get_parent_nodes())

        while to_visit:
            current = to_visit.pop()
            if current.id in visited:
                continue
            visited.add(current.id)
            ancestors.append(current)

            for parent in current.get_parent_nodes():
                if parent.id not in visited:
                    to_visit.append(parent)

        return ancestors

    def _get_local_execution_order(self) -> List["NodeModel"]:
        """
        Get execution order for this node and its ancestors using local topological sort.

        Uses Kahn's algorithm on the subset of nodes (ancestors + self).

        Returns:
            List of nodes in execution order

        Raises:
            ValueError: If cyclic dependency is detected
        """
        # Get all ancestors + self
        ancestors = self._get_all_ancestors()
        nodes = ancestors + [self]
        node_ids = {node.id for node in nodes}

        # Build adjacency list and in-degree count (only within subset)
        in_degree = defaultdict(int)
        adjacency = defaultdict(list)

        for node in nodes:
            if node.id not in in_degree:
                in_degree[node.id] = 0

            for output_conn in node.outputs().values():
                for connected_input in output_conn.connections():
                    if connected_input.node and connected_input.node.id in node_ids:
                        target_id = connected_input.node.id
                        adjacency[node.id].append(target_id)
                        in_degree[target_id] += 1

        # Kahn's algorithm (topological sort)
        node_map = {node.id: node for node in nodes}
        queue = deque(node.id for node in nodes if in_degree[node.id] == 0)
        sorted_nodes = []

        while queue:
            node_id = queue.popleft()
            sorted_nodes.append(node_map[node_id])

            for neighbor_id in adjacency[node_id]:
                in_degree[neighbor_id] -= 1
                if in_degree[neighbor_id] == 0:
                    queue.append(neighbor_id)

        # Check for cycles
        if len(sorted_nodes) != len(nodes):
            cyclic_nodes = [node.name for node in nodes if node not in sorted_nodes]
            raise ValueError(f"Cyclic dependency detected in nodes: {', '.join(cyclic_nodes)}")

        return sorted_nodes

    def get_output_value(self, output_name: str) -> Any:
        """Get the value of an output connector."""
        if self._is_dirty:
            self.cook()

        return self._cached_outputs.get(output_name)

    # Serialization

    def serialize(self) -> dict:
        """
        Serialize node to dictionary.

        Uses Pydantic's model_dump() which automatically excludes non-serializable fields.
        """
        data = self.model_dump(mode="json")
        data["position"] = self._position

        # Serialize parameters
        data["parameters"] = {
            name: param.serialize()
            for name, param in self._parameters.items()
        }

        # Serialize connectors
        data["inputs"] = {
            name: conn.serialize()
            for name, conn in self._inputs.items()
        }

        data["outputs"] = {
            name: conn.serialize()
            for name, conn in self._outputs.items()
        }

        return data

    @classmethod
    def deserialize(cls, data: dict, network: Optional["NetworkModel"] = None) -> "NodeModel":
        """Deserialize node from dictionary."""
        node_id = data.get("id", uuid4())
        if isinstance(node_id, str):
            node_id = UUID(node_id)

        node_data = {
            "name": data.get("name", "Node"),
            "node_type": data.get("node_type", "BaseNode"),
            "category": data.get("category", "General"),
            "id": node_id,
            "color": data.get("color"),
        }

        node = cls.model_validate(node_data)
        node.network = network

        node._position = data.get("position", (0.0, 0.0))

        # Deserialize parameters
        for name, param_data in data.get("parameters", {}).items():
            param = ParameterModel.deserialize(param_data)
            node._parameters[name] = param
            param.value_changed.connect(node._on_parameter_changed)

        # Deserialize connectors
        for name, conn_data in data.get("inputs", {}).items():
            conn = ConnectorModel.deserialize(conn_data, node)
            node._inputs[name] = conn
            conn.connected_changed.connect(node.mark_dirty)

        for name, conn_data in data.get("outputs", {}).items():
            conn = ConnectorModel.deserialize(conn_data, node)
            node._outputs[name] = conn

        return node

    def __repr__(self) -> str:
        return f"NodeModel(id='{str(self.id)[:8]}...', name='{self.name}', type='{self.node_type}')"
