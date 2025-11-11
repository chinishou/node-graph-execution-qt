"""
Data Type Registry
==================

Registry for managing data types in the node graph system.
Supports both built-in types and custom user-defined types.
"""

from typing import Type, Dict, List, Any, Optional, Callable, Tuple
from collections import OrderedDict


class DataTypeRegistry:
    """
    Global registry for data types.

    This registry maintains an ordered list of available data types
    and provides type conversion capabilities.

    Features:
    - Ordered menu of built-in types (int, float, str, bool)
    - Custom type registration (e.g., pathlib.Path, numpy.ndarray)
    - Type conversion with custom converters
    - Type compatibility checking

    Example::

        # Register a custom type
        from pathlib import Path
        DataTypeRegistry.register("Path", Path)

        # Register with custom converter
        DataTypeRegistry.register("Vector3", Vector3,
                                   converter=lambda x: Vector3(*x) if isinstance(x, (list, tuple)) else x)

        # Use in nodes
        self.add_input("file_path", data_type="Path")

        # Get all types for UI dropdown
        all_types = DataTypeRegistry.get_ordered_types()  # ["int", "float", "str", "bool", "Path", "Vector3"]
    """

    # Ordered dictionary to maintain insertion order for UI display
    _types: OrderedDict[str, Type] = OrderedDict()

    # Custom type converters (optional)
    _converters: Dict[str, Callable[[Any], Any]] = {}

    # Type conversion rules (from_type, to_type) -> converter_func
    _conversion_rules: Dict[Tuple[str, str], Callable[[Any], Any]] = {}

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

        # Built-in type converters (basic Python type conversion)
        cls._converters["int"] = int
        cls._converters["float"] = float
        cls._converters["str"] = str
        cls._converters["bool"] = bool
        cls._converters["any"] = lambda x: x

        # Built-in conversion rules
        cls._add_builtin_conversion_rules()

        cls._initialized = True

    @classmethod
    def _add_builtin_conversion_rules(cls):
        """Add built-in type conversion rules."""
        # Numeric conversions
        cls._conversion_rules[("int", "float")] = float
        cls._conversion_rules[("float", "int")] = int

        # String conversions
        cls._conversion_rules[("int", "str")] = str
        cls._conversion_rules[("float", "str")] = str
        cls._conversion_rules[("bool", "str")] = str
        cls._conversion_rules[("str", "int")] = int
        cls._conversion_rules[("str", "float")] = float

        # Boolean conversions
        cls._conversion_rules[("int", "bool")] = bool
        cls._conversion_rules[("float", "bool")] = bool
        cls._conversion_rules[("str", "bool")] = lambda x: x.lower() in ("true", "1", "yes")

        # Any type can convert to itself
        for type_name in ["int", "float", "str", "bool", "any"]:
            cls._conversion_rules[(type_name, type_name)] = lambda x: x

    @classmethod
    def register(
        cls,
        name: str,
        type_class: Type,
        converter: Optional[Callable[[Any], Any]] = None,
        description: str = "",
    ) -> None:
        """
        Register a custom data type.

        Args:
            name: Type name (will appear in UI dropdown)
            type_class: Python type/class
            converter: Optional custom converter function
            description: Optional description for documentation

        Example::

            from pathlib import Path
            DataTypeRegistry.register("Path", Path)

            # With custom converter
            DataTypeRegistry.register(
                "Vector3",
                Vector3,
                converter=lambda x: Vector3(*x) if isinstance(x, (list, tuple)) else x
            )
        """
        cls._initialize_builtin_types()

        # Register type
        cls._types[name] = type_class

        # Register converter
        if converter is not None:
            cls._converters[name] = converter
        else:
            # Default: use type_class as converter
            cls._converters[name] = type_class

        # Add self-conversion rule
        cls._conversion_rules[(name, name)] = lambda x: x

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
            if name in cls._converters:
                del cls._converters[name]
            # Remove related conversion rules
            cls._conversion_rules = {
                k: v for k, v in cls._conversion_rules.items()
                if k[0] != name and k[1] != name
            }
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
    def convert(cls, value: Any, target_type: str) -> Any:
        """
        Convert a value to target type.

        Args:
            value: Value to convert
            target_type: Target type name

        Returns:
            Converted value

        Raises:
            ValueError: If conversion fails
            KeyError: If target_type is not registered
        """
        cls._initialize_builtin_types()

        # Special case: "any" type accepts everything
        if target_type == "any":
            return value

        # Get converter
        if target_type not in cls._converters:
            raise KeyError(f"Data type '{target_type}' is not registered")

        converter = cls._converters[target_type]

        try:
            return converter(value)
        except Exception as e:
            raise ValueError(f"Failed to convert {value} to {target_type}: {e}")

    @classmethod
    def can_convert(cls, from_type: str, to_type: str) -> bool:
        """
        Check if conversion from one type to another is possible.

        Args:
            from_type: Source type name
            to_type: Target type name

        Returns:
            True if conversion is possible
        """
        cls._initialize_builtin_types()

        # "any" type is compatible with everything
        if from_type == "any" or to_type == "any":
            return True

        # Same type is always compatible
        if from_type == to_type:
            return True

        # Check if conversion rule exists
        return (from_type, to_type) in cls._conversion_rules

    @classmethod
    def add_conversion_rule(
        cls,
        from_type: str,
        to_type: str,
        converter: Callable[[Any], Any]
    ) -> None:
        """
        Add a custom conversion rule between two types.

        Args:
            from_type: Source type name
            to_type: Target type name
            converter: Conversion function

        Example::

            # Add conversion from Vector3 to float (magnitude)
            DataTypeRegistry.add_conversion_rule(
                "Vector3", "float",
                lambda v: v.length()
            )
        """
        cls._initialize_builtin_types()
        cls._conversion_rules[(from_type, to_type)] = converter

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
        cls._converters = {k: v for k, v in cls._converters.items() if k in builtin_types}
        cls._conversion_rules = {
            k: v for k, v in cls._conversion_rules.items()
            if k[0] in builtin_types and k[1] in builtin_types
        }

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
            "has_converter": name in cls._converters,
            "default_value": cls.get_default_value(name),
        }

    @classmethod
    def reset(cls) -> None:
        """Reset registry to initial state (for testing)."""
        cls._types.clear()
        cls._converters.clear()
        cls._conversion_rules.clear()
        cls._initialized = False
        cls._initialize_builtin_types()


# Initialize built-in types on module import
DataTypeRegistry._initialize_builtin_types()
