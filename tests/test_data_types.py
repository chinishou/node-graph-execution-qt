"""
Tests for DataTypeRegistry
===========================

Test the data type registry system including:
- Built-in types (ordered menu)
- Custom type registration
- Type conversion
- Type compatibility checking
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodegraph.core import DataTypeRegistry


def test_builtin_types():
    """Test built-in types are registered in order."""
    types = DataTypeRegistry.get_ordered_types()

    assert 'int' in types
    assert 'float' in types
    assert 'str' in types
    assert 'bool' in types
    assert 'any' in types

    # Check order (built-in types come first)
    expected_start = ['int', 'float', 'str', 'bool', 'any']
    assert types[:5] == expected_start

    print("✓ Built-in types registered correctly")


def test_custom_type_registration():
    """Test registering custom types."""
    # Register a custom type
    DataTypeRegistry.register("Path", Path, description="File system path")

    # Check it's registered
    assert DataTypeRegistry.is_registered("Path")

    # Check it appears in the types list
    types = DataTypeRegistry.get_ordered_types()
    assert "Path" in types

    # Get type info
    info = DataTypeRegistry.get_type_info("Path")
    assert info is not None
    assert info["name"] == "Path"
    assert info["type_class"] == Path

    print("✓ Custom type registration works")


def test_type_conversion():
    """Test type conversion between built-in types."""
    # int to float
    result = DataTypeRegistry.convert(3, "float")
    assert result == 3.0
    assert isinstance(result, float)

    # float to int
    result = DataTypeRegistry.convert(3.14, "int")
    assert result == 3
    assert isinstance(result, int)

    # int to str
    result = DataTypeRegistry.convert(42, "str")
    assert result == "42"
    assert isinstance(result, str)

    # str to int
    result = DataTypeRegistry.convert("123", "int")
    assert result == 123
    assert isinstance(result, int)

    # str to float
    result = DataTypeRegistry.convert("3.14", "float")
    assert result == 3.14
    assert isinstance(result, float)

    # any type accepts everything
    result = DataTypeRegistry.convert([1, 2, 3], "any")
    assert result == [1, 2, 3]

    print("✓ Type conversion works")


def test_type_compatibility():
    """Test type compatibility checking."""
    # int and float are compatible
    assert DataTypeRegistry.can_convert("int", "float")
    assert DataTypeRegistry.can_convert("float", "int")

    # String conversions
    assert DataTypeRegistry.can_convert("int", "str")
    assert DataTypeRegistry.can_convert("float", "str")
    assert DataTypeRegistry.can_convert("str", "int")
    assert DataTypeRegistry.can_convert("str", "float")

    # any type is compatible with everything
    assert DataTypeRegistry.can_convert("any", "float")
    assert DataTypeRegistry.can_convert("int", "any")

    # Same type is always compatible
    assert DataTypeRegistry.can_convert("int", "int")
    assert DataTypeRegistry.can_convert("str", "str")

    print("✓ Type compatibility checking works")


def test_default_values():
    """Test default value generation for types."""
    assert DataTypeRegistry.get_default_value("int") == 0
    assert DataTypeRegistry.get_default_value("float") == 0.0
    assert DataTypeRegistry.get_default_value("str") == ""
    assert DataTypeRegistry.get_default_value("bool") == False
    assert DataTypeRegistry.get_default_value("any") is None

    print("✓ Default value generation works")


def test_custom_type_converter():
    """Test custom type with custom converter."""
    # Register a custom type with converter
    class Vector3:
        def __init__(self, x=0, y=0, z=0):
            self.x, self.y, self.z = x, y, z

        def __repr__(self):
            return f"Vector3({self.x}, {self.y}, {self.z})"

    def list_to_vector3(value):
        if isinstance(value, (list, tuple)) and len(value) == 3:
            return Vector3(*value)
        elif isinstance(value, Vector3):
            return value
        else:
            return Vector3()

    DataTypeRegistry.register("Vector3", Vector3, converter=list_to_vector3)

    # Test conversion
    vec = DataTypeRegistry.convert([1, 2, 3], "Vector3")
    assert isinstance(vec, Vector3)
    assert vec.x == 1 and vec.y == 2 and vec.z == 3

    print("✓ Custom type with converter works")


def test_unregister_type():
    """Test unregistering a type."""
    # Register a temporary type
    class TempType:
        pass

    DataTypeRegistry.register("TempType", TempType)
    assert DataTypeRegistry.is_registered("TempType")

    # Unregister it
    result = DataTypeRegistry.unregister("TempType")
    assert result == True
    assert not DataTypeRegistry.is_registered("TempType")

    print("✓ Type unregistration works")


def run_all_tests():
    """Run all DataTypeRegistry tests."""
    print("=" * 60)
    print("DataTypeRegistry Tests")
    print("=" * 60)

    test_builtin_types()
    test_custom_type_registration()
    test_type_conversion()
    test_type_compatibility()
    test_default_values()
    test_custom_type_converter()
    test_unregister_type()

    print("=" * 60)
    print("All DataTypeRegistry tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
