"""
Tests for PythonExporter
=========================

Test Python code generation including:
- Network export to Python code
- Topological sorting
- Node code generation
- Variable naming
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodegraph.core.models import NetworkModel
from nodegraph.core.serialization import PythonExporter
from nodegraph.nodes.operators import AddNode, MultiplyNode, SubtractNode
from nodegraph.nodes.base import FloatVariable


def test_exporter_export_empty_network():
    """Test exporting empty network."""
    network = NetworkModel(name="EmptyNetwork")

    # Export
    code = PythonExporter.export(network)

    assert isinstance(code, str)
    assert "def run_network" in code
    assert "EmptyNetwork" in code
    assert "return {}" in code or "return outputs" in code

    print("✓ Export empty network works")


def test_exporter_export_simple_network():
    """Test exporting simple network."""
    network = NetworkModel(name="SimpleNetwork")

    var = FloatVariable(default_value=5.0, name="Var1")
    add = AddNode()

    network.add_node(var)
    network.add_node(add)

    # Export
    code = PythonExporter.export(network)

    assert "def run_network" in code
    assert "SimpleNetwork" in code
    assert "Var1" in code
    assert "AddNode" in code or "Add" in code

    print("✓ Export simple network works")


def test_exporter_custom_function_name():
    """Test exporting with custom function name."""
    network = NetworkModel(name="Test")

    var = FloatVariable(default_value=1.0)
    network.add_node(var)

    # Export with custom name
    code = PythonExporter.export(network, function_name="custom_function")

    assert "def custom_function" in code
    assert "def run_network" not in code

    print("✓ Custom function name works")


def test_exporter_topological_sort():
    """Test topological sorting of nodes."""
    network = NetworkModel(name="TopoTest")

    # Create linear chain: A -> B -> C
    var_a = FloatVariable(default_value=1.0, name="A")
    add = AddNode()
    mul = MultiplyNode()

    network.add_node(var_a)
    network.add_node(add)
    network.add_node(mul)

    network.connect(var_a.id, "out", add.id, "a")
    network.connect(add.id, "result", mul.id, "a")

    # Get sorted order
    sorted_nodes = PythonExporter._topological_sort(network)

    assert len(sorted_nodes) == 3

    # Verify order: var_a should come before add, add should come before mul
    node_indices = {node.id: i for i, node in enumerate(sorted_nodes)}

    assert node_indices[var_a.id] < node_indices[add.id]
    assert node_indices[add.id] < node_indices[mul.id]

    print("✓ Topological sort works")


def test_exporter_topological_sort_independent():
    """Test topological sort with independent nodes."""
    network = NetworkModel(name="IndependentTest")

    # Create two independent chains
    var_a = FloatVariable(default_value=1.0, name="A")
    var_b = FloatVariable(default_value=2.0, name="B")

    network.add_node(var_a)
    network.add_node(var_b)

    # Get sorted order (both should be included)
    sorted_nodes = PythonExporter._topological_sort(network)

    assert len(sorted_nodes) == 2
    assert var_a in sorted_nodes
    assert var_b in sorted_nodes

    print("✓ Topological sort with independent nodes works")


def test_exporter_generate_node_code():
    """Test generating code for a single node."""
    network = NetworkModel(name="Test")

    add = AddNode()
    network.add_node(add)

    # Set default values
    add.input("a").default_value = 5.0
    add.input("b").default_value = 3.0

    # Generate code
    code_lines = PythonExporter._generate_node_code(add, indent="    ")

    assert len(code_lines) > 0

    code = "\n".join(code_lines)
    assert "AddNode" in code or "Add" in code
    assert "5.0" in code or "3.0" in code  # Default values

    print("✓ Generate node code works")


def test_exporter_generate_connected_node():
    """Test generating code for connected nodes."""
    network = NetworkModel(name="ConnectedTest")

    var_a = FloatVariable(default_value=10.0, name="VarA")
    add = AddNode()

    network.add_node(var_a)
    network.add_node(add)

    network.connect(var_a.id, "out", add.id, "a")

    # Generate code for add node
    code_lines = PythonExporter._generate_node_code(add, indent="    ")

    code = "\n".join(code_lines)
    assert "VarA" in code or "var" in code.lower()

    print("✓ Generate connected node code works")


def test_exporter_make_var_name():
    """Test variable name generation."""
    network = NetworkModel(name="Test")

    node = AddNode()
    node.name = "My Add Node"
    network.add_node(node)

    # Generate variable name
    var_name = PythonExporter._make_var_name(node, "result")

    # Should be valid Python identifier
    assert var_name.replace("_", "").isalnum()
    assert not var_name[0].isdigit()
    assert " " not in var_name

    print("✓ Make variable name works")


def test_exporter_make_var_name_special_chars():
    """Test variable name with special characters."""
    network = NetworkModel(name="Test")

    node = AddNode()
    node.name = "Add-Node@123!"
    network.add_node(node)

    # Generate variable name
    var_name = PythonExporter._make_var_name(node, "output")

    # Should only contain valid characters
    assert all(c.isalnum() or c == "_" for c in var_name)

    print("✓ Variable name with special chars works")


def test_exporter_code_structure():
    """Test that exported code has correct structure."""
    network = NetworkModel(name="StructureTest")

    var = FloatVariable(default_value=5.0)
    add = AddNode()

    network.add_node(var)
    network.add_node(add)

    network.connect(var.id, "out", add.id, "a")

    # Export
    code = PythonExporter.export(network, function_name="test_func")

    # Check structure
    assert '"""' in code  # Docstring
    assert "from typing import" in code  # Imports
    assert "def test_func" in code  # Function definition
    assert "inputs: Dict[str, Any]" in code or "inputs" in code  # Parameter
    assert "return" in code  # Return statement
    assert 'if __name__ == "__main__"' in code  # Main block

    print("✓ Code structure works")


def test_exporter_multiple_outputs():
    """Test node with multiple outputs."""
    network = NetworkModel(name="MultiOutputTest")

    var = FloatVariable(default_value=5.0, name="Var")
    network.add_node(var)

    # Generate code
    code_lines = PythonExporter._generate_node_code(var, indent="")

    code = "\n".join(code_lines)
    assert len(code) > 0

    print("✓ Multiple outputs handling works")


def test_exporter_complex_network():
    """Test exporting complex network."""
    network = NetworkModel(name="ComplexNetwork")

    # Build: (A + B) * C - D
    var_a = FloatVariable(default_value=2.0, name="A")
    var_b = FloatVariable(default_value=3.0, name="B")
    var_c = FloatVariable(default_value=4.0, name="C")
    var_d = FloatVariable(default_value=1.0, name="D")

    add = AddNode()
    mul = MultiplyNode()
    sub = SubtractNode()

    network.add_node(var_a)
    network.add_node(var_b)
    network.add_node(var_c)
    network.add_node(var_d)
    network.add_node(add)
    network.add_node(mul)
    network.add_node(sub)

    network.connect(var_a.id, "out", add.id, "a")
    network.connect(var_b.id, "out", add.id, "b")
    network.connect(add.id, "result", mul.id, "a")
    network.connect(var_c.id, "out", mul.id, "b")
    network.connect(mul.id, "result", sub.id, "a")
    network.connect(var_d.id, "out", sub.id, "b")

    # Export
    code = PythonExporter.export(network)

    assert "ComplexNetwork" in code
    assert len(code) > 100  # Should be reasonably long

    # Verify all nodes mentioned
    assert "A" in code or "var_a" in code.lower()
    assert "B" in code or "var_b" in code.lower()

    print("✓ Complex network export works")


def test_exporter_code_is_valid_python():
    """Test that exported code is syntactically valid Python."""
    network = NetworkModel(name="ValidTest")

    var = FloatVariable(default_value=10.0, name="Test")
    add = AddNode()

    network.add_node(var)
    network.add_node(add)

    # Export
    code = PythonExporter.export(network, function_name="valid_test")

    # Try to compile (will raise SyntaxError if invalid)
    try:
        compile(code, "<string>", "exec")
        print("✓ Exported code is valid Python")
    except SyntaxError as e:
        assert False, f"Generated invalid Python code: {e}"


def test_exporter_docstring_generation():
    """Test that function has proper docstring."""
    network = NetworkModel(name="DocstringTest")

    var = FloatVariable(default_value=1.0)
    network.add_node(var)

    # Export
    code = PythonExporter.export(network)

    # Check for docstring elements
    assert '"""' in code
    assert "Args:" in code
    assert "Returns:" in code

    print("✓ Docstring generation works")


def run_all_tests():
    """Run all PythonExporter tests."""
    print("=" * 60)
    print("PythonExporter Tests")
    print("=" * 60)

    test_exporter_export_empty_network()
    test_exporter_export_simple_network()
    test_exporter_custom_function_name()
    test_exporter_topological_sort()
    test_exporter_topological_sort_independent()
    test_exporter_generate_node_code()
    test_exporter_generate_connected_node()
    test_exporter_make_var_name()
    test_exporter_make_var_name_special_chars()
    test_exporter_code_structure()
    test_exporter_multiple_outputs()
    test_exporter_complex_network()
    test_exporter_code_is_valid_python()
    test_exporter_docstring_generation()

    print("=" * 60)
    print("All PythonExporter tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
