"""
Node Model
==========

Represents a node in the network graph.
Nodes are the fundamental building blocks that process data.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, TYPE_CHECKING, Tuple
from uuid import uuid4
from .parameter_model import ParameterModel
from .connector_model import ConnectorModel, ConnectorType
from ..signals import Signal

if TYPE_CHECKING:
    from .network_model import NetworkModel


@dataclass
class NodeModel:
    """
    Data model for a node.

    Nodes are the processing units in a network. They have inputs, outputs,
    and parameters that control their behavior. Similar to Houdini's nodes.

    Attributes:
        name: Node display name
        node_type: Type of node (e.g., "AddNode", "SubnetNode")
        category: Category for organization (e.g., "Math", "Logic")
        id: Unique node identifier (UUID)
        network: The network this node belongs to
        color: Optional custom color
        parameters: Dictionary of parameters
        inputs: Dictionary of input connectors
        outputs: Dictionary of output connectors
        dirty_changed: Signal emitted when dirty state changes
        position_changed: Signal emitted when position changes
    """

    name: str = "Node"
    node_type: str = "BaseNode"
    category: str = "General"
    network: Optional["NetworkModel"] = None
    id: str = field(default_factory=lambda: str(uuid4()))
    color: Optional[str] = None

    # Position (stored as tuple for easy serialization)
    _position: Tuple[float, float] = field(default=(0.0, 0.0), repr=False)

    # Node components (non-serializable, will be handled separately)
    _parameters: Dict[str, ParameterModel] = field(init=False, repr=False, default_factory=dict)
    _inputs: Dict[str, ConnectorModel] = field(init=False, repr=False, default_factory=dict)
    _outputs: Dict[str, ConnectorModel] = field(init=False, repr=False, default_factory=dict)

    # Execution state
    _is_dirty: bool = field(init=False, repr=False, default=True)
    _is_cooking: bool = field(init=False, repr=False, default=False)
    _cached_outputs: Dict[str, Any] = field(init=False, repr=False, default_factory=dict)
    _cook_error: Optional[str] = field(init=False, repr=False, default=None)

    # Signals
    dirty_changed: Signal = field(init=False, repr=False, compare=False)
    position_changed: Signal = field(init=False, repr=False, compare=False)
    parameter_changed: Signal = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        """Initialize non-dataclass fields after construction."""
        self._parameters = {}
        self._inputs = {}
        self._outputs = {}
        self._is_dirty = True
        self._is_cooking = False
        self._cached_outputs = {}
        self._cook_error = None

        # Initialize signals
        self.dirty_changed = Signal()
        self.position_changed = Signal()
        self.parameter_changed = Signal()

    def position(self) -> Tuple[float, float]:
        """Get node position."""
        return self._position

    def set_position(self, x: float, y: float, emit_signal: bool = True) -> None:
        """Set node position."""
        old_pos = self._position
        self._position = (x, y)

        if emit_signal and old_pos != self._position:
            self.position_changed.emit(x, y)

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
        self.parameter_changed.emit()

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

    # Execution (cooking)

    def mark_dirty(self) -> None:
        """Mark this node as dirty (needs recomputation)."""
        if not self._is_dirty:
            self._is_dirty = True
            self._cached_outputs.clear()
            self._cook_error = None

            # Propagate dirty state to outputs
            for output in self._outputs.values():
                output.mark_dirty()

            self.dirty_changed.emit(True)

    def is_dirty(self) -> bool:
        """Check if node needs recomputation."""
        return self._is_dirty

    def cook(self) -> bool:
        """
        Execute this node (Houdini terminology: "cook").

        Returns:
            True if cooking was successful, False if error occurred
        """
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

            # Call the implementation-specific cook method
            output_values = self._cook_internal(**input_values)

            # Store outputs (even if empty dict)
            if output_values is not None:
                self._cached_outputs = output_values
            else:
                self._cached_outputs = {}

            # Mark as clean
            self._is_dirty = False
            self.dirty_changed.emit(False)

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

    def get_output_value(self, output_name: str) -> Any:
        """Get the value of an output connector."""
        # Cook if dirty
        if self._is_dirty:
            self.cook()

        return self._cached_outputs.get(output_name)

    def cook_error(self) -> Optional[str]:
        """Get the last cook error message if any."""
        return self._cook_error

    # Serialization

    def serialize(self) -> Dict[str, Any]:
        """Serialize node to dictionary."""
        # Use dataclass asdict for basic fields
        data = {
            "id": self.id,
            "name": self.name,
            "node_type": self.node_type,
            "category": self.category,
            "position": self._position,
            "color": self.color,
        }

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
    def deserialize(cls, data: Dict[str, Any], network: Optional["NetworkModel"] = None) -> "NodeModel":
        """Deserialize node from dictionary."""
        # Create node with basic fields
        node = cls(
            name=data.get("name", "Node"),
            node_type=data.get("node_type", "BaseNode"),
            category=data.get("category", "General"),
            network=network,
            id=data.get("id", str(uuid4())),
            color=data.get("color"),
        )

        # Set position
        node.set_position(*data.get("position", (0, 0)), emit_signal=False)

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
        return f"NodeModel(id='{self.id[:8]}...', name='{self.name}', type='{self.node_type}')"
