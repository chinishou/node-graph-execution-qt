"""
Connector Model
===============

Represents an input or output port on a node (connector in Houdini terminology).
Connectors allow data to flow between nodes.
"""

from typing import Optional, Any, List, TYPE_CHECKING
from enum import Enum
from pydantic import BaseModel, Field, PrivateAttr
from ..signals import Signal

if TYPE_CHECKING:
    from .node_model import NodeModel


class ConnectorType(Enum):
    """Type of connector (input or output)."""
    INPUT = "input"
    OUTPUT = "output"


class ConnectorModel(BaseModel):
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
    node: Optional["NodeModel"] = Field(default=None, exclude=True)  # Exclude from serialization
    default_value: Any = None
    description: str = ""

    # Private attributes (using PrivateAttr for Pydantic V2)
    _connections: List["ConnectorModel"] = PrivateAttr(default_factory=list)
    _cached_value: Any = PrivateAttr(default=None)
    _is_dirty: bool = PrivateAttr(default=True)
    _connected_changed: Signal = PrivateAttr(default=None)

    model_config = {
        "arbitrary_types_allowed": True,  # Allow Signal and NodeModel types
    }

    def model_post_init(self, __context) -> None:
        """Initialize fields after Pydantic validation."""
        # Set display name
        if self.display_name is None:
            self.display_name = self.name

        # Initialize signal
        self._connected_changed = Signal()

    @property
    def connected_changed(self) -> Signal:
        """Get connected_changed signal (compatibility property)."""
        return self._connected_changed

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
            self._connected_changed.emit()
            other._connected_changed.emit()

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
            self._connected_changed.emit()
            other._connected_changed.emit()

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

        # Check data type compatibility (strict)
        # "any" type is compatible with everything
        if self.data_type == "any" or other.data_type == "any":
            return True

        # Other types must match exactly
        return self.data_type == other.data_type

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

    def serialize(self) -> dict:
        """
        Serialize connector to dictionary.

        Uses Pydantic's model_dump() which automatically excludes non-serializable fields.
        """
        data = self.model_dump(mode="json")
        # Convert ConnectorType enum to string
        data["connector_type"] = self.connector_type.value
        return data

    @classmethod
    def deserialize(cls, data: dict, node: Optional["NodeModel"] = None) -> "ConnectorModel":
        """
        Deserialize connector from dictionary.

        Args:
            data: Dictionary containing connector data
            node: The node this connector belongs to

        Returns:
            ConnectorModel instance
        """
        # Convert connector_type string to enum if needed
        if "connector_type" in data and isinstance(data["connector_type"], str):
            data["connector_type"] = ConnectorType(data["connector_type"])

        # Create connector using Pydantic's model_validate
        connector = cls.model_validate(data)
        connector.node = node

        return connector

    def __repr__(self) -> str:
        conn_type = "INPUT" if self.is_input() else "OUTPUT"
        return f"ConnectorModel(name='{self.name}', type={conn_type}, data_type='{self.data_type}')"
