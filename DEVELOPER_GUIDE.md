# Developer Guide

Node Graph Execution Qt - Developer Documentation

## Table of Contents

1. [Getting Started](#getting-started)
2. [Architecture Overview](#architecture-overview)
3. [Creating Custom Nodes](#creating-custom-nodes)
4. [Type System](#type-system)
5. [Polymorphic Design Pattern](#polymorphic-design-pattern)
6. [Subnet Nodes](#subnet-nodes)
7. [Serialization](#serialization)
8. [Testing](#testing)
9. [Best Practices](#best-practices)

---

## Getting Started

### Development Setup

```bash
# Clone the repository
git clone https://github.com/chinishou/node-graph-execution-qt.git
cd node-graph-execution-qt

# Install in development mode with all dependencies
pip install -e ".[all]"

# Run tests
pytest tests/ -v

# Run the editor
python run_editor.py
```

### Project Structure

```
nodegraph/
├── core/                      # Core models (business logic)
│   ├── models/                # Data models
│   │   ├── network_model.py   # Network graph
│   │   ├── node_model.py      # Node base model
│   │   ├── connector_model.py # Input/output connectors
│   │   └── parameter_model.py # Node parameters
│   ├── serialization/         # JSON/Python export
│   └── data_types.py          # Type registry
├── nodes/                     # Built-in nodes
│   ├── base/                  # Base node classes
│   ├── operators/             # Math/logic operators
│   ├── subnet/                # Subnet nodes
│   └── utils/                 # Utility nodes
└── views/                     # Qt UI layer
    ├── network/               # Network view/scene
    ├── nodes/                 # Node graphics items
    └── widgets/               # UI widgets
```

---

## Architecture Overview

### Three-Layer Architecture

1. **Model Layer** (`nodegraph/core/`)
   - Pure Python business logic
   - No Qt dependencies
   - Can run headless (CLI, testing)

2. **View Layer** (`nodegraph/views/`)
   - Qt graphics rendering
   - User interaction handling
   - Visual representation only

3. **Node Library** (`nodegraph/nodes/`)
   - Reusable node implementations
   - Domain-specific functionality
   - Extensible via plugins

### Key Design Principles

1. **Model-View Separation**: Core logic independent from UI
2. **Polymorphic Design**: Extensible without modifying core code
3. **Type Safety**: Automatic type conversion and validation
4. **Pydantic Models**: Type-safe data models with validation

---

## Creating Custom Nodes

### Basic Node Structure

```python
from typing import Dict, Any
from nodegraph.nodes.base import BaseNode

class MyCustomNode(BaseNode):
    """Custom node description."""

    category: str = "Custom"  # Node category for palette
    description: str = "What this node does"

    def __init__(self, **kwargs):
        super().__init__(name="MyNode", node_type="MyCustomNode", **kwargs)

    def setup(self) -> None:
        """Define inputs, outputs, and parameters."""
        # Add inputs
        self.add_input("input1", data_type="float", default_value=0.0, label="Input 1")
        self.add_input("input2", data_type="int", default_value=1, label="Input 2")

        # Add parameters
        self.add_parameter(
            "multiplier",
            data_type="float",
            default_value=1.0,
            label="Multiplier"
        )

        # Add outputs
        self.add_output("result", data_type="float", label="Result")

    def compute(self, **inputs) -> Dict[str, Any]:
        """Execute node logic.

        Args:
            **inputs: Dictionary of input values

        Returns:
            Dictionary of output values
        """
        input1 = inputs.get("input1", 0.0)
        input2 = inputs.get("input2", 1)
        multiplier = self.parameter("multiplier").value()

        result = (input1 + input2) * multiplier

        return {"result": result}
```

### Node Registration

```python
from nodegraph.core.registry import NodeRegistry

# Register your node
NodeRegistry.register(MyCustomNode)

# Create instances
node = NodeRegistry.create_node("MyCustomNode")
```

---

## Type System

### Supported Data Types

- `int`: Integer numbers
- `float`: Floating-point numbers
- `str`: Strings
- `bool`: Boolean values
- `any`: Dynamic type (with automatic conversion)

### Automatic Type Conversion

The system automatically converts connector default values based on `data_type`:

```python
# Example: Math node with string input from UI
add_node.input("b").default_value = "3"  # String from UI

# Automatically converted to:
# - int if data_type="int": 3
# - float if data_type="float": 3.0
# - int if data_type="any" and no decimal: 3
```

**Conversion Logic** (`ConnectorModel._convert_value()`):

| data_type | Input: "123" | Input: "3.14" | Input: "text" |
|-----------|-------------|---------------|---------------|
| `int`     | → 123       | → 3           | → 0 (default) |
| `float`   | → 123.0     | → 3.14        | → 0.0 (default)|
| `str`     | → "123"     | → "3.14"      | → "text"      |
| `any`     | → 123       | → 3.14        | → "text"      |

### Color Coding

Each data type has a visual color in the editor:

```python
# nodegraph/core/data_types.py
DATA_TYPE_COLORS = {
    "int": "#3b7dd6",      # Blue
    "float": "#ff9500",    # Orange
    "str": "#00b74f",      # Green
    "bool": "#c9302c",     # Red
    "any": "#888888",      # Gray
}
```

---

## Polymorphic Design Pattern

### Problem

Previously, the UI layer had hardcoded type checks for specific nodes:

```python
# Bad: Hardcoded checks
if node_type == 'SubnetNode' and is_output:
    # Special logic for SubnetNode
elif node_type == 'ConvertNode':
    # Special logic for ConvertNode
```

This violates the Open-Closed Principle and makes the system fragile.

### Solution: Polymorphic Methods

Nodes override virtual methods for custom behavior:

```python
class BaseNode:
    def resolve_connector_display_type(
        self,
        connector_name: str,
        is_output: bool,
        visited: Optional[set] = None
    ) -> Optional[str]:
        """Override for custom type resolution logic.

        Returns:
            Type string (e.g., "int", "float") or None for default
        """
        return None  # Default: use connector's data_type

    def transforms_data_type(self) -> bool:
        """Indicate if this node transforms data types.

        Returns:
            True if node changes input type to different output type
        """
        return False  # Default: preserve input types
```

### Example: ConvertNode

```python
class ConvertNode(BaseNode):
    def transforms_data_type(self) -> bool:
        """ConvertNode explicitly transforms types."""
        return True  # Don't use pass-through logic
```

### Example: SubnetNode

```python
class SubnetNode(BaseNode):
    def resolve_connector_display_type(
        self,
        connector_name: str,
        is_output: bool,
        visited: Optional[set] = None
    ) -> Optional[str]:
        """Resolve by looking into internal network."""
        if not is_output or not self._internal_network:
            return None

        # Find corresponding SubnetOutputNode
        for node in self._internal_network.nodes():
            if isinstance(node, SubnetOutputNode):
                if node.get_connector_name() == connector_name:
                    # Get type from connected node inside subnet
                    internal_input = node.input(connector_name)
                    if internal_input and internal_input.is_connected():
                        connections = internal_input.connections()
                        if connections:
                            connected_connector = connections[0]
                            return connected_connector.data_type

        return None
```

### UI Layer Uses Polymorphism

```python
# Good: Polymorphic call
if self.connector.node:
    custom_type = self.connector.node.resolve_connector_display_type(
        self.connector.name,
        self.is_output,
        visited
    )
    if custom_type:
        return custom_type
```

**Benefits**:
- New node types don't require UI changes
- Each node encapsulates its own logic
- System is extensible without modification

---

## Subnet Nodes

### Creating a Subnet

Subnets encapsulate subgraphs as reusable nodes:

```python
from nodegraph.nodes.subnet.subnet_node import SubnetNode

# Create subnet
subnet = SubnetNode(name="MySubnet")
network.add_node(subnet)

# Access internal network
internal_net = subnet.get_internal_network()

# Add nodes inside subnet
add_node = AddNode()
internal_net.add_node(add_node)

# Create I/O nodes
input_node = SubnetInputNode(connector_name="input1", data_type="float")
output_node = SubnetOutputNode(connector_name="output1", data_type="float")
internal_net.add_node(input_node)
internal_net.add_node(output_node)

# Connect: input -> add -> output
input_node.output("input1").connect_to(add_node.input("a"))
add_node.output("result").connect_to(output_node.input("output1"))

# Sync connectors (creates external ports)
subnet.sync_io_nodes()
```

### Recursive Type Resolution

SubnetNodes support chaining:

```
float(1) -> subnet1(input->convert(int)->output) -> subnet2(input->...)
```

Type resolution traverses the chain:
1. subnet2's internal input checks parent's external connection
2. Parent is subnet1's output
3. subnet1's output calls `resolve_connector_display_type()`
4. Returns type from internal convert node
5. Type propagates back to subnet2's internal input

**Implementation**:
```python
# SubnetInputNode.resolve_connector_display_type()
connected_node = connected_connector.node

# Recursively resolve if connected node supports it
if hasattr(connected_node, 'resolve_connector_display_type'):
    custom_type = connected_node.resolve_connector_display_type(
        connected_connector.name,
        True,  # is_output
        visited  # Prevent cycles
    )
    if custom_type:
        return custom_type
```

---

## Serialization

### JSON Format

```json
{
  "version": "1.0",
  "name": "MyNetwork",
  "nodes": {
    "uuid-1": {
      "node_type": "AddNode",
      "name": "Add",
      "position": [100, 200],
      "parameters": {
        "type": "float"
      },
      "inputs": {
        "a": {"default_value": 5.0},
        "b": {"default_value": 3.0}
      }
    }
  },
  "connections": [
    {
      "source_node": "uuid-1",
      "source_connector": "result",
      "target_node": "uuid-2",
      "target_connector": "value"
    }
  ]
}
```

### Saving and Loading

```python
from nodegraph.core.serialization import JSONSerializer

# Save
serializer = JSONSerializer()
serializer.save(network, "mynetwork.json")

# Load
loaded_network = serializer.load("mynetwork.json")
```

### Custom Serialization

Override `serialize()` and `deserialize()` for custom data:

```python
class MyCustomNode(BaseNode):
    def serialize(self) -> dict:
        data = super().serialize()
        data["custom_field"] = self._custom_data
        return data

    @classmethod
    def deserialize(cls, data: dict) -> "MyCustomNode":
        node = super().deserialize(data)
        node._custom_data = data.get("custom_field")
        return node
```

---

## Testing

### Unit Testing Nodes

```python
import pytest
from nodegraph.core import NetworkModel
from nodegraph.nodes.operators import AddNode

def test_add_node():
    """Test AddNode computation."""
    network = NetworkModel(name="test")

    node = AddNode()
    network.add_node(node)

    # Set inputs
    node.input("a").default_value = 5.0
    node.input("b").default_value = 3.0

    # Execute
    result = node.execute()

    # Assert
    assert result is True
    assert node.get_output_value("result") == 8.0
```

### UI Testing with pytest-qt

```python
import pytest
from PySide6.QtCore import Qt
from nodegraph.views.main_window import MainWindow

@pytest.fixture
def main_window(qtbot):
    """Create main window fixture."""
    window = MainWindow()
    qtbot.addWidget(window)
    return window

def test_create_node_with_tab(qtbot, main_window):
    """Test creating node with Tab key."""
    view = main_window.network_view
    scene = view.scene()

    # Press Tab key
    qtbot.keyPress(view, Qt.Key_Tab)

    # Check menu appears
    assert scene._node_menu is not None
    assert scene._node_menu.isVisible()
```

### Testing Type Conversion

```python
def test_type_conversion():
    """Test automatic type conversion for default values."""
    network = NetworkModel(name="test")

    add_node = AddNode()
    network.add_node(add_node)

    # Simulate UI string input
    add_node.input("b").default_value = "3"  # String

    # Get value (should be converted to float)
    value = add_node.input("b").get_value()

    assert isinstance(value, (int, float))
    assert value == 3.0
```

---

## Best Practices

### 1. Always Define `setup()` Method

Don't define connectors in `__init__()`. Use `setup()`:

```python
# Good
class MyNode(BaseNode):
    def setup(self):
        self.add_input("input1", data_type="float")
        self.add_output("output1", data_type="float")

# Bad
class MyNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.add_input("input1", data_type="float")  # Wrong!
```

### 2. Use Type Annotations

```python
from typing import Dict, Any

def compute(self, **inputs) -> Dict[str, Any]:
    """Always annotate return type."""
    return {"result": 0.0}
```

### 3. Handle Missing Inputs

```python
def compute(self, **inputs) -> Dict[str, Any]:
    # Use .get() with defaults
    a = inputs.get("a", 0.0)
    b = inputs.get("b", 0.0)

    return {"result": a + b}
```

### 4. Prevent Infinite Recursion

When implementing `resolve_connector_display_type()`:

```python
def resolve_connector_display_type(
    self,
    connector_name: str,
    is_output: bool,
    visited: Optional[set] = None
) -> Optional[str]:
    # Always check visited set
    if visited is None:
        visited = set()

    connector_id = id(some_connector)
    if connector_id in visited:
        return None  # Cycle detected
    visited.add(connector_id)

    # Your logic here
```

### 5. Document Your Nodes

```python
class MyNode(BaseNode):
    """
    One-line description.

    Longer description of what this node does,
    how it should be used, and any important notes.

    Inputs:
        input1 (float): Description of input1
        input2 (int): Description of input2

    Outputs:
        result (float): Description of output

    Parameters:
        multiplier (float): Multiply factor
    """
```

### 6. Error Handling

```python
def compute(self, **inputs) -> Dict[str, Any]:
    try:
        a = inputs.get("a", 0.0)
        b = inputs.get("b", 0.0)

        if b == 0:
            print(f"Warning: Division by zero in node '{self.name}'")
            return {"result": 0.0}

        result = a / b
        return {"result": result}

    except Exception as e:
        print(f"Error in {self.name}: {e}")
        return {"result": None}
```

### 7. Avoid Hardcoded Type Checks

```python
# Bad
if node.node_type == "SubnetNode":
    # Special handling

# Good: Use polymorphism
result = node.resolve_connector_display_type(...)
```

---

## Advanced Topics

### Custom Type Resolution

For nodes that need special type display logic:

```python
class MyTransformNode(BaseNode):
    def resolve_connector_display_type(
        self,
        connector_name: str,
        is_output: bool,
        visited: Optional[set] = None
    ) -> Optional[str]:
        """Custom type resolution."""
        if is_output and connector_name == "transformed":
            # Always show as specific type
            return self.parameter("output_type").value()
        return None

    def transforms_data_type(self) -> bool:
        """This node transforms types."""
        return True
```

### Extending the Type System

Add custom data types:

```python
from nodegraph.core.data_types import DataTypeRegistry

# Register custom type
DataTypeRegistry.register_type(
    "vector3",
    default_value=(0.0, 0.0, 0.0),
    color="#ff00ff"
)

# Use in nodes
self.add_input("position", data_type="vector3")
```

### Node Callbacks

Listen to node events:

```python
node.dirty_changed.connect(on_dirty_changed)
node.cooked.connect(on_cooked)
parameter.value_changed.connect(on_parameter_changed)
```

---

## Contributing

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings (Google style)
- Maximum line length: 100 characters

### Pull Request Process

1. Create feature branch: `git checkout -b feature/my-feature`
2. Write tests for new functionality
3. Ensure all tests pass: `pytest tests/ -v`
4. Update documentation
5. Submit PR with clear description

### Debugging Tips

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Print node execution
node._debug = True
node.execute()  # Will print inputs/outputs

# Inspect network state
print(network.nodes())
print(network.connections())
```

---

## Resources

- [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed architecture
- [USER_GUIDE.md](USER_GUIDE.md) - User manual
- [API Reference](docs/api_reference.md) - API documentation
- [Examples](examples/) - Example code

---

## Support

- GitHub Issues: [Report bugs or request features](https://github.com/chinishou/node-graph-execution-qt/issues)
- Discussions: [Ask questions](https://github.com/chinishou/node-graph-execution-qt/discussions)
