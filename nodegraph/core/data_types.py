"""
Data Type Registry
==================

Registry for managing data types in the node graph system.
Supports both built-in types and custom user-defined types.

Note: Type conversion is NOT automatic. Use explicit conversion nodes
when you need to convert between types (e.g., IntToFloat node).
"""

from typing import Type, Dict, List, Any, Optional
from collections import OrderedDict


class DataTypeRegistry:
    """
    Global registry for data types.

    This registry maintains an ordered list of available data types.

    Features:
    - Ordered menu of built-in types (int, float, str, bool)
    - Custom type registration (e.g., pathlib.Path, numpy.ndarray)

    Example::

        # Register a custom type
        from pathlib import Path
        DataTypeRegistry.register("Path", Path)

        # Use in nodes
        self.add_input("file_path", data_type="Path")

        # Get all types for UI dropdown
        all_types = DataTypeRegistry.get_ordered_types()
    """

    # Ordered dictionary to maintain insertion order for UI display
    _types: OrderedDict[str, Type] = OrderedDict()

    # Flag to track if built-in types have been initialized
    _initialized = False

    @classmethod
    def _initialize_builtin_types(cls):
        """Initialize built-in data types (called automatically)."""
        if cls._initialized:
            return

        # Ordered menu of built-in types
        cls._types["int"] = int
        cls._types["float"] = float
        cls._types["str"] = str
        cls._types["bool"] = bool
        cls._types["any"] = object  # Special type that accepts anything

        cls._initialized = True

    @classmethod
    def register(
        cls,
        name: str,
        type_class: Type,
        description: str = "",
    ) -> None:
        """
        Register a custom data type.

        Args:
            name: Type name (will appear in UI dropdown)
            type_class: Python type/class
            description: Optional description for documentation

        Example::

            from pathlib import Path
            DataTypeRegistry.register("Path", Path)
        """
        cls._initialize_builtin_types()

        # Register type
        cls._types[name] = type_class

    @classmethod
    def unregister(cls, name: str) -> bool:
        """
        Unregister a data type.

        Args:
            name: Type name to unregister

        Returns:
            True if successful, False if type not found
        """
        if name in cls._types:
            del cls._types[name]
            return True
        return False

    @classmethod
    def get_type(cls, name: str) -> Optional[Type]:
        """
        Get type class by name.

        Args:
            name: Type name

        Returns:
            Type class or None if not found
        """
        cls._initialize_builtin_types()
        return cls._types.get(name)

    @classmethod
    def get_ordered_types(cls) -> List[str]:
        """
        Get all registered type names in order.

        This is the ordered menu for UI dropdowns.
        Built-in types appear first, followed by custom types in registration order.

        Returns:
            Ordered list of type names
        """
        cls._initialize_builtin_types()
        return list(cls._types.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if a type is registered."""
        cls._initialize_builtin_types()
        return name in cls._types

    @classmethod
    def get_default_value(cls, type_name: str) -> Any:
        """
        Get default value for a type.

        Args:
            type_name: Type name

        Returns:
            Default value for the type
        """
        cls._initialize_builtin_types()

        defaults = {
            "int": 0,
            "float": 0.0,
            "str": "",
            "bool": False,
            "any": None,
        }

        if type_name in defaults:
            return defaults[type_name]

        # For custom types, try to instantiate with no args
        type_class = cls.get_type(type_name)
        if type_class is not None:
            try:
                return type_class()
            except:
                return None

        return None

    @classmethod
    def clear_custom_types(cls) -> None:
        """Clear all custom types (keeps built-in types)."""
        cls._initialize_builtin_types()

        builtin_types = ["int", "float", "str", "bool", "any"]

        # Remove custom types
        cls._types = OrderedDict((k, v) for k, v in cls._types.items() if k in builtin_types)

    @classmethod
    def get_type_info(cls, name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a registered type.

        Args:
            name: Type name

        Returns:
            Dictionary with type information or None if not found
        """
        cls._initialize_builtin_types()

        if name not in cls._types:
            return None

        type_class = cls._types[name]

        return {
            "name": name,
            "type_class": type_class,
            "module": type_class.__module__ if hasattr(type_class, "__module__") else None,
            "default_value": cls.get_default_value(name),
        }

    @classmethod
    def reset(cls) -> None:
        """Reset registry to initial state (for testing)."""
        cls._types.clear()
        cls._initialized = False
        cls._initialize_builtin_types()


# Initialize built-in types on module import
DataTypeRegistry._initialize_builtin_types()
