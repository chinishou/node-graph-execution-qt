"""
Node Registry
=============

Global registry for node types.
Allows registration and instantiation of custom node classes.
"""

from typing import Dict, Type, List, Optional
import inspect


class NodeRegistry:
    """
    Global registry for node types.

    This is a singleton that manages all available node types.
    Users can register their custom nodes and create instances by type name.

    Example::

        # Register a node class
        NodeRegistry.register(AddNode)

        # Create a node instance
        node = NodeRegistry.create_node("AddNode")

        # Get all registered nodes
        nodes = NodeRegistry.get_all_nodes()
    """

    _instance = None
    _nodes: Dict[str, Type] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, node_class: Type, node_type: Optional[str] = None) -> None:
        """
        Register a node class.

        Args:
            node_class: The node class to register (must inherit from BaseNode)
            node_type: Optional custom type name (defaults to class name)
        """
        # Validate that it's a node class
        if not hasattr(node_class, '__mro__'):
            raise ValueError(f"Invalid node class: {node_class}")

        if node_type is None:
            node_type = node_class.__name__

        # Check if already registered
        if node_type in cls._nodes:
            print(f"Warning: Node type '{node_type}' is already registered. Overwriting.")

        cls._nodes[node_type] = node_class

        print(f"Registered node: {node_type}")

    @classmethod
    def unregister(cls, node_type: str) -> bool:
        """
        Unregister a node type.

        Args:
            node_type: The type name to unregister

        Returns:
            True if unregistered successfully
        """
        if node_type in cls._nodes:
            del cls._nodes[node_type]
            return True
        return False

    @classmethod
    def is_registered(cls, node_type: str) -> bool:
        """Check if a node type is registered."""
        return node_type in cls._nodes

    @classmethod
    def get_node_class(cls, node_type: str) -> Optional[Type]:
        """Get the class for a node type."""
        return cls._nodes.get(node_type)

    @classmethod
    def create_node(cls, node_type: str, **kwargs):
        """
        Create a node instance by type name.

        Args:
            node_type: The type name of the node
            **kwargs: Additional arguments to pass to the node constructor

        Returns:
            Node instance

        Raises:
            ValueError: If node type is not registered
        """
        node_class = cls.get_node_class(node_type)

        if node_class is None:
            raise ValueError(f"Node type '{node_type}' is not registered")

        return node_class(**kwargs)

    @classmethod
    def get_all_nodes(cls) -> Dict[str, Type]:
        """Get all registered node types."""
        return cls._nodes.copy()

    @classmethod
    def get_nodes_by_category(cls, category: str) -> Dict[str, Type]:
        """
        Get all nodes in a specific category.

        Args:
            category: The category name

        Returns:
            Dictionary of node types in that category
        """
        result = {}

        for node_type, node_class in cls._nodes.items():
            if hasattr(node_class, 'category') and node_class.category == category:
                result[node_type] = node_class

        return result

    @classmethod
    def get_categories(cls) -> List[str]:
        """Get all unique category names."""
        categories = set()

        for node_class in cls._nodes.values():
            if hasattr(node_class, 'category'):
                categories.add(node_class.category)

        return sorted(categories)

    @classmethod
    def get_node_info(cls, node_type: str) -> Optional[Dict[str, any]]:
        """
        Get information about a node type.

        Args:
            node_type: The type name

        Returns:
            Dictionary with node information (category, description, etc.)
        """
        node_class = cls.get_node_class(node_type)

        if node_class is None:
            return None

        info = {
            "type": node_type,
            "class": node_class.__name__,
            "category": getattr(node_class, 'category', 'General'),
            "description": getattr(node_class, 'description', ''),
            "module": node_class.__module__,
        }

        if node_class.__doc__:
            info["docstring"] = inspect.cleandoc(node_class.__doc__)

        return info

    @classmethod
    def register_module(cls, module) -> int:
        """
        Register all node classes from a module.

        Args:
            module: Python module containing node classes

        Returns:
            Number of nodes registered
        """
        count = 0

        for name in dir(module):
            obj = getattr(module, name)

            # Check if it's a class and likely a node
            if inspect.isclass(obj) and name.endswith('Node'):
                try:
                    cls.register(obj)
                    count += 1
                except Exception as e:
                    print(f"Failed to register {name}: {e}")

        return count

    @classmethod
    def clear(cls) -> None:
        """Clear all registered nodes."""
        cls._nodes.clear()

    def __repr__(self) -> str:
        return f"NodeRegistry(nodes={len(self._nodes)})"
