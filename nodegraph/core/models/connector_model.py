"""
Connector Model
===============

Represents an input or output port on a node (connector in Houdini terminology).
Connectors allow data to flow between nodes.
"""

from typing import Optional, Any, Dict, TYPE_CHECKING
from enum import Enum
from ..signals import Signal

if TYPE_CHECKING:
    from .node_model import NodeModel


class ConnectorType(Enum):
    """Type of connector (input or output)."""
    INPUT = "input"
    OUTPUT = "output"


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
        multi_connection: Whether multiple connections are allowed (inputs only)
        default_value: Default value if no connection
        connected_changed: Signal emitted when connection state changes
    """

    def __init__(
        self,
        name: str,
        connector_type: ConnectorType,
        data_type: str = "any",
        display_name: Optional[str] = None,
        node: Optional["NodeModel"] = None,
        multi_connection: bool = False,
        default_value: Any = None,
        description: str = "",
    ):
        self.name = name
        self.connector_type = connector_type
        self.data_type = data_type
        self.display_name = display_name or name
        self.node = node
        self.multi_connection = multi_connection
        self.default_value = default_value
        self.description = description

        # Store connections (for outputs: list of connectors, for inputs: single/multiple connectors)
        self._connections: list["ConnectorModel"] = []

        # Cached value (for data flow)
        self._cached_value: Any = None
        self._is_dirty: bool = True

        # Signals
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

        # For inputs, check if multi-connection is allowed
        if self.is_input() and not self.multi_connection and len(self._connections) > 0:
            # Disconnect existing connection first
            self.disconnect_all()

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

    def connections(self) -> list["ConnectorModel"]:
        """Get list of connected connectors."""
        return self._connections.copy()

    def _can_connect_to(self, other: "ConnectorModel") -> bool:
        """Check if connection to another connector is valid."""
        # Can't connect to self
        if other is self:
            return False

        # Can't connect to same node
        if other.node is self.node:
            return False

        # Input can only connect to output and vice versa
        if self.connector_type == other.connector_type:
            return False

        # Check data type compatibility (simplified - "any" matches everything)
        if self.data_type != "any" and other.data_type != "any":
            if self.data_type != other.data_type:
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
        For inputs: returns the connected output's value or default value
        """
        if self.is_output():
            # Output value comes from the node's cook result
            if self.node:
                return self.node.get_output_value(self.name)
            return None
        else:
            # Input value comes from connected output or default
            if self.is_connected():
                # Get value from first connected output
                source = self._connections[0]
                return source.get_value()
            return self.default_value

    def serialize(self) -> Dict[str, Any]:
        """Serialize connector to dictionary."""
        return {
            "name": self.name,
            "connector_type": self.connector_type.value,
            "data_type": self.data_type,
            "display_name": self.display_name,
            "multi_connection": self.multi_connection,
            "default_value": self.default_value,
            "description": self.description,
        }

    @classmethod
    def deserialize(cls, data: Dict[str, Any], node: Optional["NodeModel"] = None) -> "ConnectorModel":
        """Deserialize connector from dictionary."""
        connector_type = ConnectorType(data.get("connector_type", "input"))
        return cls(
            name=data["name"],
            connector_type=connector_type,
            data_type=data.get("data_type", "any"),
            display_name=data.get("display_name"),
            node=node,
            multi_connection=data.get("multi_connection", False),
            default_value=data.get("default_value"),
            description=data.get("description", ""),
        )

    def __repr__(self) -> str:
        conn_type = "INPUT" if self.is_input() else "OUTPUT"
        return f"ConnectorModel(name='{self.name}', type={conn_type}, data_type='{self.data_type}')"
