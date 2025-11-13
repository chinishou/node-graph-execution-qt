"""
Tests for DataTypeRegistry
===========================

Test the data type registry system including:
- Built-in types (ordered menu)
- Custom type registration
- Default value generation
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


def test_default_values():
    """Test default value generation for types."""
    assert DataTypeRegistry.get_default_value("int") == 0
    assert DataTypeRegistry.get_default_value("float") == 0.0
    assert DataTypeRegistry.get_default_value("str") == ""
    assert DataTypeRegistry.get_default_value("bool") == False
    assert DataTypeRegistry.get_default_value("any") is None

    print("✓ Default value generation works")


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
    test_default_values()
    test_unregister_type()

    print("=" * 60)
    print("All DataTypeRegistry tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
