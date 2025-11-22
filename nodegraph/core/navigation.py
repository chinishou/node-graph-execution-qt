"""
Network Navigation
==================

System for navigating between network levels (root and subnets).
"""

from typing import List, Optional, Tuple
from PySide6.QtCore import QObject, Signal
from uuid import UUID
from .models import NetworkModel, NodeModel


class NetworkLocation:
    """Represents a location in the network hierarchy."""

    def __init__(self, network: NetworkModel, parent_node: Optional[NodeModel] = None,
                 path: Optional[List[Tuple[str, UUID]]] = None):
        """
        Initialize network location.

        Args:
            network: The network at this location
            parent_node: The subnet node containing this network (None for root)
            path: List of (node_name, node_id) tuples from root to this location
        """
        self.network = network
        self.parent_node = parent_node
        self.path = path or []

    def get_path_string(self) -> str:
        """Get the path as a string (e.g., '/network/subnet1/subnet2')."""
        if not self.path:
            return "/" + self.network.name

        parts = [self.network.name if not self.path else self.path[0][0]]
        parts.extend([name for name, _ in self.path[1:]])

        return "/" + "/".join(parts)

    def get_depth(self) -> int:
        """Get the depth level (0 for root)."""
        return len(self.path)

    def copy(self) -> "NetworkLocation":
        """Create a copy of this location."""
        return NetworkLocation(
            network=self.network,
            parent_node=self.parent_node,
            path=self.path.copy()
        )


class NavigationController(QObject):
    """
    Controls navigation between network levels.

    Provides:
    - Current location tracking
    - History (back/forward)
    - Path-based navigation
    """

    # Signals
    location_changed = Signal(object)  # NetworkLocation
    can_go_back_changed = Signal(bool)
    can_go_forward_changed = Signal(bool)

    def __init__(self, root_network: NetworkModel, parent=None):
        super().__init__(parent)

        self._root_network = root_network
        self._current_location = NetworkLocation(root_network)

        # History for back/forward navigation
        self._history: List[NetworkLocation] = [self._current_location.copy()]
        self._history_index = 0

    def get_current_location(self) -> NetworkLocation:
        """Get the current location."""
        return self._current_location

    def get_current_network(self) -> NetworkModel:
        """Get the current network."""
        return self._current_location.network

    def get_root_network(self) -> NetworkModel:
        """Get the root network."""
        return self._root_network

    def can_go_back(self) -> bool:
        """Check if can go back in history."""
        return self._history_index > 0

    def can_go_forward(self) -> bool:
        """Check if can go forward in history."""
        return self._history_index < len(self._history) - 1

    def go_back(self) -> bool:
        """Go back in history."""
        if not self.can_go_back():
            return False

        self._history_index -= 1
        self._current_location = self._history[self._history_index].copy()

        self._emit_signals()
        return True

    def go_forward(self) -> bool:
        """Go forward in history."""
        if not self.can_go_forward():
            return False

        self._history_index += 1
        self._current_location = self._history[self._history_index].copy()

        self._emit_signals()
        return True

    def go_up(self) -> bool:
        """Go up one level to parent network."""
        if self._current_location.get_depth() == 0:
            return False  # Already at root

        # Navigate to parent
        parent_path = self._current_location.path[:-1]

        if not parent_path:
            # Go to root
            return self.navigate_to_root()
        else:
            # Navigate to parent subnet
            return self.navigate_to_path(parent_path)

    def navigate_to_root(self) -> bool:
        """Navigate to the root network."""
        new_location = NetworkLocation(self._root_network)
        return self._navigate_to(new_location)

    def navigate_to_subnet(self, subnet_node: NodeModel) -> bool:
        """
        Navigate into a subnet node.

        Args:
            subnet_node: The SubnetNode to enter

        Returns:
            True if navigation successful
        """
        from ..nodes.subnet import SubnetNode

        if not isinstance(subnet_node, SubnetNode):
            return False

        # Get the internal network
        internal_network = subnet_node.get_internal_network()
        if not internal_network:
            return False

        # Create new path
        new_path = self._current_location.path.copy()
        new_path.append((subnet_node.name, subnet_node.id))

        # Create new location
        new_location = NetworkLocation(
            network=internal_network,
            parent_node=subnet_node,
            path=new_path
        )

        return self._navigate_to(new_location)

    def navigate_to_path(self, path: List[Tuple[str, UUID]]) -> bool:
        """
        Navigate to a specific path.

        Args:
            path: List of (node_name, node_id) tuples

        Returns:
            True if navigation successful
        """
        from ..nodes.subnet import SubnetNode

        # Start from root
        current_network = self._root_network
        current_node = None

        # Follow the path
        for i, (node_name, node_id) in enumerate(path):
            # Find the node in current network
            node = current_network.get_node(node_id)

            if not node or not isinstance(node, SubnetNode):
                return False  # Path is invalid

            # Move into this subnet
            current_node = node
            current_network = node.get_internal_network()

            if not current_network:
                return False  # Subnet has no internal network

        # Create location for this path
        new_location = NetworkLocation(
            network=current_network,
            parent_node=current_node,
            path=path
        )

        return self._navigate_to(new_location)

    def navigate_to_depth(self, depth: int) -> bool:
        """
        Navigate to a specific depth in current path.

        Args:
            depth: 0 for root, 1 for first subnet level, etc.

        Returns:
            True if navigation successful
        """
        current_depth = self._current_location.get_depth()

        if depth < 0 or depth > current_depth:
            return False

        if depth == 0:
            return self.navigate_to_root()
        else:
            # Navigate to path up to specified depth
            target_path = self._current_location.path[:depth]
            return self.navigate_to_path(target_path)

    def _navigate_to(self, new_location: NetworkLocation) -> bool:
        """
        Internal method to navigate to a new location.

        Updates history and emits signals.
        """
        # Update current location
        self._current_location = new_location.copy()

        # Clear forward history
        self._history = self._history[:self._history_index + 1]

        # Add to history
        self._history.append(self._current_location.copy())
        self._history_index = len(self._history) - 1

        # Emit signals
        self._emit_signals()

        return True

    def _emit_signals(self):
        """Emit all navigation-related signals."""
        self.location_changed.emit(self._current_location)
        self.can_go_back_changed.emit(self.can_go_back())
        self.can_go_forward_changed.emit(self.can_go_forward())

    def get_path_components(self) -> List[Tuple[str, int]]:
        """
        Get path components for UI display.

        Returns:
            List of (name, depth) tuples for each level in the path
        """
        if not self._current_location.path:
            return [(self._root_network.name, 0)]

        components = [(self._root_network.name, 0)]

        for i, (node_name, node_id) in enumerate(self._current_location.path):
            components.append((node_name, i + 1))

        return components
