"""
Node Model
==========

Represents a node in the network graph.
Nodes are the fundamental building blocks that process data.
"""

from typing import Dict, Any, Optional, TYPE_CHECKING, Tuple
from uuid import uuid4
from pydantic import BaseModel, Field, PrivateAttr
from .parameter_model import ParameterModel
from .connector_model import ConnectorModel, ConnectorType
from ..signals import Signal

if TYPE_CHECKING:
    from .network_model import NetworkModel


class NodeModel(BaseModel):
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
    network: Optional["NetworkModel"] = Field(default=None, exclude=True)
    id: str = Field(default_factory=lambda: str(uuid4()))
    color: Optional[str] = None
    enable_caching: bool = False  # Enable dirty state tracking and output caching

    # Private attributes (using PrivateAttr for Pydantic V2)
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
        # Initialize signals
        self._dirty_changed = Signal()
        self._position_changed = Signal()
        self._parameter_changed = Signal()

    @property
    def dirty_changed(self) -> Signal:
        """Get dirty_changed signal (compatibility property)."""
        return self._dirty_changed

    @property
    def position_changed(self) -> Signal:
        """Get position_changed signal (compatibility property)."""
        return self._position_changed

    @property
    def parameter_changed(self) -> Signal:
        """Get parameter_changed signal (compatibility property)."""
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
        Execute this node (Houdini terminology: "cook").

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

            # Call the implementation-specific cook method
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

    def serialize(self) -> dict:
        """Serialize node to dictionary using Pydantic."""
        # Use Pydantic's model_dump for basic fields (private attrs are auto-excluded)
        data = self.model_dump()

        # Add position
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
        """Deserialize node from dictionary using Pydantic."""
        # Create node with basic fields using Pydantic
        node_data = {
            "name": data.get("name", "Node"),
            "node_type": data.get("node_type", "BaseNode"),
            "category": data.get("category", "General"),
            "id": data.get("id", str(uuid4())),
            "color": data.get("color"),
        }

        node = cls.model_validate(node_data)
        node.network = network

        # Set position (private attribute)
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
        return f"NodeModel(id='{self.id[:8]}...', name='{self.name}', type='{self.node_type}')"
