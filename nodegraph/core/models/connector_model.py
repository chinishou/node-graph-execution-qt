"""
Connector Model
===============

Represents an input or output port on a node (connector in Houdini terminology).
Connectors allow data to flow between nodes.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Any, Dict, List, TYPE_CHECKING
from enum import Enum
from ..signals import Signal
from ..data_types import DataTypeRegistry

if TYPE_CHECKING:
    from .node_model import NodeModel


class ConnectorType(Enum):
    """Type of connector (input or output)."""
    INPUT = "input"
    OUTPUT = "output"


@dataclass
class ConnectorModel:
    """
    Data model for a node connector (port).

    Connectors are the input/output ports on nodes that allow connections.
    Similar to Houdini's connectors.

    Attributes:
        name: Connector identifier
        connector_type: INPUT or OUTPUT
        data_type: Type of data this connector accepts/produces
        display_name: Human-readable name
        node: The node this connector belongs to
        default_value: Default value if no connection (inputs only)
        description: Connector description
        connected_changed: Signal emitted when connection state changes
    """

    name: str
    connector_type: ConnectorType
    data_type: str = "any"
    display_name: Optional[str] = None
    node: Optional["NodeModel"] = None
    default_value: Any = None
    description: str = ""

    # Non-serializable fields
    _connections: List["ConnectorModel"] = field(init=False, repr=False, compare=False, default_factory=list)
    _cached_value: Any = field(init=False, repr=False, compare=False, default=None)
    _is_dirty: bool = field(init=False, repr=False, compare=False, default=True)
    connected_changed: Signal = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        """Initialize non-dataclass fields after construction."""
        # Set display name
        if self.display_name is None:
            self.display_name = self.name

        # Initialize lists and signals
        self._connections = []
        self._cached_value = None
        self._is_dirty = True
        self.connected_changed = Signal()

    def is_input(self) -> bool:
        """Check if this is an input connector."""
        return self.connector_type == ConnectorType.INPUT

    def is_output(self) -> bool:
        """Check if this is an output connector."""
        return self.connector_type == ConnectorType.OUTPUT

    def connect_to(self, other: "ConnectorModel") -> bool:
        """
        Connect this connector to another connector.

        Args:
            other: The connector to connect to

        Returns:
            True if connection was successful, False otherwise
        """
        # Validate connection
        if not self._can_connect_to(other):
            return False

        # For inputs, disconnect existing connection first (single connection only)
        # Check both self and other for input connectors
        if self.is_input() and len(self._connections) > 0:
            self.disconnect_all()
        if other.is_input() and len(other._connections) > 0:
            other.disconnect_all()

        # Add connection
        if other not in self._connections:
            self._connections.append(other)
            # Also add reverse connection
            if self not in other._connections:
                other._connections.append(self)

            # Mark as dirty
            self.mark_dirty()

            # Emit signal
            self.connected_changed.emit()
            other.connected_changed.emit()

            return True

        return False

    def disconnect_from(self, other: "ConnectorModel") -> bool:
        """
        Disconnect from another connector.

        Args:
            other: The connector to disconnect from

        Returns:
            True if disconnection was successful
        """
        if other in self._connections:
            self._connections.remove(other)

            # Also remove reverse connection
            if self in other._connections:
                other._connections.remove(self)

            # Mark as dirty
            self.mark_dirty()

            # Emit signal
            self.connected_changed.emit()
            other.connected_changed.emit()

            return True

        return False

    def disconnect_all(self) -> None:
        """Disconnect all connections."""
        for conn in self._connections[:]:  # Copy to avoid modification during iteration
            self.disconnect_from(conn)

    def is_connected(self) -> bool:
        """Check if this connector has any connections."""
        return len(self._connections) > 0

    def connections(self) -> List["ConnectorModel"]:
        """Get list of connected connectors."""
        return self._connections.copy()

    def _can_connect_to(self, other: "ConnectorModel") -> bool:
        """
        Check if connection to another connector is valid.

        Args:
            other: The connector to check

        Returns:
            True if connection is valid
        """
        # Can't connect to self
        if other is self:
            return False

        # Can't connect to same node
        if other.node is self.node:
            return False

        # Input can only connect to output and vice versa
        if self.connector_type == other.connector_type:
            return False

        # Check data type compatibility using DataTypeRegistry
        if self.data_type != "any" and other.data_type != "any":
            # For strict compatibility, types must match or be convertible
            if self.data_type != other.data_type:
                # Check if conversion is possible
                if self.is_input():
                    # Check if output type can convert to input type
                    if not DataTypeRegistry.can_convert(other.data_type, self.data_type):
                        return False
                else:
                    # Check if input type can convert to output type
                    if not DataTypeRegistry.can_convert(self.data_type, other.data_type):
                        return False

        return True

    def mark_dirty(self) -> None:
        """Mark this connector (and downstream) as dirty."""
        self._is_dirty = True
        self._cached_value = None

        # Propagate dirty state downstream
        if self.is_output():
            for conn in self._connections:
                if conn.node:
                    conn.node.mark_dirty()

    def get_value(self) -> Any:
        """
        Get the value from this connector.

        For outputs: returns the node's computed output value
        For inputs: returns connected output value or default value

        Returns:
            Value from connected output or default value
        """
        if self.is_output():
            # Output value comes from the node's cook result
            if self.node:
                return self.node.get_output_value(self.name)
            return None
        else:
            # Input value: return connected value or default
            if self.is_connected():
                # Get value from connected output
                source = self._connections[0]
                return source.get_value()
            else:
                # No connection: return default value
                return self.default_value

    def serialize(self) -> Dict[str, Any]:
        """
        Serialize connector to dictionary.

        Manually creates dictionary to avoid serializing Signal objects.
        """
        return {
            "name": self.name,
            "connector_type": self.connector_type.value,
            "data_type": self.data_type,
            "display_name": self.display_name,
            "default_value": self.default_value,
            "description": self.description,
        }

    @classmethod
    def deserialize(cls, data: Dict[str, Any], node: Optional["NodeModel"] = None) -> "ConnectorModel":
        """
        Deserialize connector from dictionary.

        Args:
            data: Dictionary containing connector data
            node: The node this connector belongs to

        Returns:
            ConnectorModel instance
        """
        # Convert connector_type string to enum
        connector_type = ConnectorType(data.get("connector_type", "input"))

        # Create connector (filtering to only dataclass fields)
        connector_data = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        connector_data["connector_type"] = connector_type
        connector_data["node"] = node

        return cls(**connector_data)

    def __repr__(self) -> str:
        conn_type = "INPUT" if self.is_input() else "OUTPUT"
        return f"ConnectorModel(name='{self.name}', type={conn_type}, data_type='{self.data_type}')"
