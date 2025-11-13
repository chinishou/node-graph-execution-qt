"""
Tests for JSONSerializer
=========================

Test JSON serialization and deserialization including:
- Save/load to files
- Network serialization
- Version handling
- Error handling
- String conversion
"""

import sys
import json
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodegraph.core.models import NetworkModel
from nodegraph.core.serialization import JSONSerializer
from nodegraph.core.registry import NodeRegistry
from nodegraph.nodes.operators import AddNode, MultiplyNode
from nodegraph.nodes.base import FloatVariable


def test_serializer_serialize_network():
    """Test serializing a network to dictionary."""
    network = NetworkModel(name="TestNetwork")

    var_a = FloatVariable(default_value=10.0, name="A")
    add = AddNode()

    network.add_node(var_a)
    network.add_node(add)

    # Serialize
    data = JSONSerializer.serialize_network(network)

    assert "version" in data
    assert data["version"] == JSONSerializer.VERSION
    assert "type" in data
    assert data["type"] == "node_graph"
    assert "network" in data
    assert data["network"]["name"] == "TestNetwork"

    print("✓ Serialize network works")


def test_serializer_save_load_file():
    """Test saving and loading network to/from file."""
    # Setup registry
    NodeRegistry.clear()
    NodeRegistry.register(FloatVariable, "VariableNode")  # FloatVariable has node_type="VariableNode"
    NodeRegistry.register(AddNode)

    # Create network
    network = NetworkModel(name="SaveLoadTest")

    var_a = FloatVariable(default_value=5.0, name="VarA")
    var_b = FloatVariable(default_value=3.0, name="VarB")
    add = AddNode()

    network.add_node(var_a)
    network.add_node(var_b)
    network.add_node(add)

    network.connect(var_a.id, "out", add.id, "a")
    network.connect(var_b.id, "out", add.id, "b")

    # Save to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name

    try:
        # Save
        success = JSONSerializer.save(network, temp_path)
        assert success

        # Check file exists
        assert Path(temp_path).exists()

        # Load
        loaded_network = JSONSerializer.load(temp_path)

        assert loaded_network is not None
        assert loaded_network.name == "SaveLoadTest"
        assert len(loaded_network.nodes()) == 3
        assert len(loaded_network.connections()) == 2

        print("✓ Save/load file works")

    finally:
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)


def test_serializer_load_nonexistent():
    """Test loading non-existent file raises error."""
    try:
        JSONSerializer.load("/nonexistent/path/file.json")
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError:
        pass

    print("✓ Load non-existent file raises error")


def test_serializer_load_invalid_json():
    """Test loading invalid JSON raises error."""
    # Create temp file with invalid JSON
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{ invalid json }")
        temp_path = f.name

    try:
        JSONSerializer.load(temp_path)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Invalid JSON" in str(e) or "Invalid" in str(e)

    finally:
        Path(temp_path).unlink(missing_ok=True)

    print("✓ Load invalid JSON raises error")


def test_serializer_version_warning():
    """Test that loading different version shows warning."""
    NodeRegistry.clear()
    NodeRegistry.register(FloatVariable, "VariableNode")

    network = NetworkModel(name="VersionTest")
    var = FloatVariable(default_value=1.0)
    network.add_node(var)

    # Create data with different version
    data = JSONSerializer.serialize_network(network)
    data["version"] = "0.0"

    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        temp_path = f.name

    try:
        # Load (should show warning but work)
        loaded = JSONSerializer.load(temp_path)
        assert loaded is not None

        print("✓ Version warning works")

    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_serializer_to_json_string():
    """Test converting network to JSON string."""
    network = NetworkModel(name="StringTest")

    var = FloatVariable(default_value=5.0)
    network.add_node(var)

    # Convert to JSON string
    json_str = JSONSerializer.to_json_string(network, pretty=True)

    assert isinstance(json_str, str)
    assert "StringTest" in json_str
    assert "version" in json_str

    # Verify it's valid JSON
    data = json.loads(json_str)
    assert data["network"]["name"] == "StringTest"

    print("✓ To JSON string works")


def test_serializer_from_json_string():
    """Test creating network from JSON string."""
    NodeRegistry.clear()
    NodeRegistry.register(FloatVariable, "VariableNode")
    NodeRegistry.register(AddNode)

    # Create network
    network = NetworkModel(name="FromString")
    var = FloatVariable(default_value=10.0, name="Var")
    add = AddNode()

    network.add_node(var)
    network.add_node(add)
    network.connect(var.id, "out", add.id, "a")

    # Convert to string
    json_str = JSONSerializer.to_json_string(network)

    # Load from string
    loaded = JSONSerializer.from_json_string(json_str)

    assert loaded is not None
    assert loaded.name == "FromString"
    assert len(loaded.nodes()) == 2
    assert len(loaded.connections()) == 1

    print("✓ From JSON string works")


def test_serializer_pretty_formatting():
    """Test pretty formatting option."""
    network = NetworkModel(name="PrettyTest")

    # Pretty formatting
    pretty_str = JSONSerializer.to_json_string(network, pretty=True)
    assert "\n" in pretty_str
    assert "  " in pretty_str  # Indentation

    # Non-pretty formatting
    compact_str = JSONSerializer.to_json_string(network, pretty=False)
    assert len(compact_str) < len(pretty_str)

    print("✓ Pretty formatting works")


def test_serializer_unregistered_nodes():
    """Test deserializing network with unregistered nodes."""
    NodeRegistry.clear()
    NodeRegistry.register(FloatVariable, "VariableNode")
    NodeRegistry.register(AddNode)

    # Create network
    network = NetworkModel(name="UnregisteredTest")
    var = FloatVariable(default_value=1.0)
    add = AddNode()

    network.add_node(var)
    network.add_node(add)

    # Serialize
    json_str = JSONSerializer.to_json_string(network)

    # Clear registry (unregister AddNode)
    NodeRegistry.clear()
    NodeRegistry.register(FloatVariable, "VariableNode")

    # Load (should skip unregistered AddNode)
    loaded = JSONSerializer.from_json_string(json_str)

    # Only FloatVariable should be loaded
    assert len(loaded.nodes()) == 1

    print("✓ Unregistered nodes handling works")


def test_serializer_empty_network():
    """Test serializing empty network."""
    network = NetworkModel(name="Empty")

    # Serialize
    data = JSONSerializer.serialize_network(network)

    assert data["network"]["name"] == "Empty"
    assert len(data["network"].get("nodes", [])) == 0

    print("✓ Empty network serialization works")


def test_serializer_roundtrip():
    """Test full roundtrip: network -> JSON -> network."""
    NodeRegistry.clear()
    NodeRegistry.register(FloatVariable, "VariableNode")
    NodeRegistry.register(AddNode)
    NodeRegistry.register(MultiplyNode)

    # Create complex network
    network = NetworkModel(name="RoundtripTest")

    var_a = FloatVariable(default_value=2.0, name="A")
    var_b = FloatVariable(default_value=3.0, name="B")
    add = AddNode()
    mul = MultiplyNode()

    network.add_node(var_a)
    network.add_node(var_b)
    network.add_node(add)
    network.add_node(mul)

    network.connect(var_a.id, "out", add.id, "a")
    network.connect(var_b.id, "out", add.id, "b")
    network.connect(add.id, "result", mul.id, "a")

    # Serialize to string
    json_str = JSONSerializer.to_json_string(network)

    # Deserialize
    loaded = JSONSerializer.from_json_string(json_str)

    # Verify structure
    assert loaded.name == "RoundtripTest"
    assert len(loaded.nodes()) == 4
    assert len(loaded.connections()) == 3

    # Verify node IDs preserved
    assert loaded.get_node(var_a.id) is not None
    assert loaded.get_node(add.id) is not None

    print("✓ Full roundtrip works")


def test_serializer_save_creates_directory():
    """Test that save creates parent directories."""
    NodeRegistry.clear()
    NodeRegistry.register(FloatVariable, "VariableNode")

    network = NetworkModel(name="DirTest")
    var = FloatVariable(default_value=1.0)
    network.add_node(var)

    # Create path in non-existent directory
    temp_dir = Path(tempfile.gettempdir()) / "test_nodegraph_dir"
    temp_file = temp_dir / "test.json"

    try:
        # Save (should create directory)
        success = JSONSerializer.save(network, str(temp_file))
        assert success
        assert temp_file.exists()

        print("✓ Save creates directories works")

    finally:
        # Cleanup
        temp_file.unlink(missing_ok=True)
        temp_dir.rmdir()


def run_all_tests():
    """Run all JSONSerializer tests."""
    print("=" * 60)
    print("JSONSerializer Tests")
    print("=" * 60)

    test_serializer_serialize_network()
    test_serializer_save_load_file()
    test_serializer_load_nonexistent()
    test_serializer_load_invalid_json()
    test_serializer_version_warning()
    test_serializer_to_json_string()
    test_serializer_from_json_string()
    test_serializer_pretty_formatting()
    test_serializer_unregistered_nodes()
    test_serializer_empty_network()
    test_serializer_roundtrip()
    test_serializer_save_creates_directory()

    print("=" * 60)
    print("All JSONSerializer tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
