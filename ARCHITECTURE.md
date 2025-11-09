# Node Graph Execution Qt - Architecture Design

## Project Overview

Houdini-style node-based programming framework built with PySide6/PyQt6, supporting visual programming and code reuse.

### Core Objectives
- Provide a node-based alternative to Qt Designer
- Junior developers: Quickly understand and modify through node tools
- Senior developers: Focus on optimizing underlying code
- Maximize code (node) reusability

### Technology Stack
- **UI Framework**: PySide6/PyQt6 (QtPy compatibility layer)
- **Python**: 3.8+
- **Serialization**: JSON
- **Future Separation**: node-graph-core (business logic core)

---

## Core Architecture Design

### Three-Layer Architecture (Inspired by QtNodes)

```
┌─────────────────────────────────────────────────┐
│         Application Layer (UI)                  │
│  - NetworkEditor (Main editor)                  │
│  - ParametersPane (Property panel)              │
│  - NodePalette (Node palette)                   │
└─────────────────────────────────────────────────┘
                      ↓↑
┌─────────────────────────────────────────────────┐
│         View Layer (Qt Graphics)                │
│  - NetworkView (QGraphicsView)                  │
│  - NodeGraphicsItem (Node graphics item)        │
│  - ConnectorGraphicsItem (Connection line)      │
└─────────────────────────────────────────────────┘
                      ↓↑
┌─────────────────────────────────────────────────┐
│         Model Layer (Core Logic)                │
│  - NetworkModel (Graph data model)              │
│  - NodeModel (Node data)                        │
│  - ParameterModel (Parameter data)              │
│  - ConnectorModel (Connection data)             │
└─────────────────────────────────────────────────┘
                      ↓↑
┌─────────────────────────────────────────────────┐
│    Future: node-graph-core (Logic separation)   │
│  - Execution engine                             │
│  - Data flow evaluation                         │
│  - Python code generation                       │
└─────────────────────────────────────────────────┘
```

### Decoupling Strategy

**Complete Model-View Separation**
- Model layer has no dependencies on Qt Widgets
- Model can run headless (CLI, testing)
- View layer only handles visualization

**Plugin Interface**
- Node registry system: `NodeRegistry`
- Parameter type system: `ParameterTypeRegistry`
- Execution engine interface: `ExecutionEngine` (future separation to core)

---

## Directory Structure

```
node-graph-execution-qt/
├── nodegraph/                    # Main package
│   ├── __init__.py
│   ├── core/                     # Core model layer (future migration to node-graph-core)
│   │   ├── __init__.py
│   │   ├── models/               # Data models
│   │   │   ├── network_model.py
│   │   │   ├── node_model.py
│   │   │   ├── parameter_model.py
│   │   │   └── connector_model.py
│   │   ├── registry/             # Registry system
│   │   │   ├── node_registry.py
│   │   │   └── parameter_registry.py
│   │   ├── serialization/        # Serialization
│   │   │   ├── json_serializer.py
│   │   │   └── python_exporter.py
│   │   └── execution/            # Execution engine (placeholder, future separation)
│   │       ├── executor.py
│   │       └── evaluator.py
│   │
│   ├── views/                    # View layer
│   │   ├── __init__.py
│   │   ├── network/              # Network view
│   │   │   ├── network_view.py
│   │   │   ├── network_scene.py
│   │   │   └── layout_manager.py
│   │   ├── nodes/                # Node graphics items
│   │   │   ├── base_node_item.py
│   │   │   ├── python_node_item.py
│   │   │   └── subnet_node_item.py
│   │   ├── connectors/           # Connection lines
│   │   │   ├── connector_item.py
│   │   │   └── connector_painter.py
│   │   └── widgets/              # UI widgets
│   │       ├── parameters_pane.py
│   │       ├── node_palette.py
│   │       └── code_editor.py
│   │
│   ├── nodes/                    # Built-in node library
│   │   ├── __init__.py
│   │   ├── base/                 # Base nodes
│   │   │   ├── base_node.py
│   │   │   ├── python_node.py
│   │   │   └── subnet_node.py
│   │   ├── operators/            # Operator nodes
│   │   ├── logic/                # Logic nodes
│   │   └── utils/                # Utility nodes
│   │
│   ├── parameters/               # Parameter type system
│   │   ├── __init__.py
│   │   ├── base_parameter.py
│   │   ├── int_parameter.py
│   │   ├── float_parameter.py
│   │   ├── string_parameter.py
│   │   └── color_parameter.py
│   │
│   └── utils/                    # Utility modules
│       ├── undo_stack.py
│       ├── logger.py
│       └── houdini_colors.py
│
├── examples/                     # Examples
│   ├── basic_network.py
│   ├── custom_node.py
│   └── subnet_example.py
│
├── tests/                        # Tests
│   ├── test_models/
│   ├── test_serialization/
│   └── test_nodes/
│
├── docs/                         # Documentation
│   ├── getting_started.md
│   ├── custom_nodes.md
│   └── api_reference.md
│
├── requirements.txt
├── setup.py
├── pyproject.toml
└── README.md
```

---

## Development Priority

### Phase 1: Core Architecture (P0 - Highest Priority)

#### 1.1 Data Model Layer
- [x] `NetworkModel` - Graph data structure
- [x] `NodeModel` - Node base class
- [x] `ParameterModel` - Parameter system
- [x] `ConnectorModel` - Connection model

#### 1.2 Node System
- [x] `BaseNode` - Base node abstract class
- [x] `PythonNode` - Python code node
- [x] `SubnetNode` - Subnet node
- [x] `NodeRegistry` - Node registry system

#### 1.3 Parameter System
- [x] `BaseParameter` - Parameter base class
- [x] Basic types: int, float, string, bool
- [x] `ParametersPane` - Property panel UI

#### 1.4 Custom Node API
```python
from nodegraph.nodes.base import BaseNode
from nodegraph.parameters import FloatParameter, StringParameter

class MyCustomNode(BaseNode):
    """Custom node example"""

    category = "Custom"

    def __init__(self):
        super().__init__()

        # Define inputs
        self.add_input("input1", data_type="float")
        self.add_input("input2", data_type="float")

        # Define outputs
        self.add_output("result", data_type="float")

        # Define parameters
        self.add_parameter("multiplier", FloatParameter(default=1.0))

    def compute(self, **inputs):
        """Execute node logic"""
        val1 = inputs.get("input1", 0.0)
        val2 = inputs.get("input2", 0.0)
        multiplier = self.parameter("multiplier").value()

        result = (val1 + val2) * multiplier
        return {"result": result}
```

### Phase 2: View Layer (P1)

#### 2.1 Basic Rendering
- [ ] `NetworkView` - QGraphicsView main view
- [ ] `NetworkScene` - QGraphicsScene
- [ ] `BaseNodeItem` - Node graphics item (Houdini style)
- [ ] `ConnectorItem` - Connection line rendering

#### 2.2 Interaction
- [ ] Drag and drop to create nodes
- [ ] Drag to connect
- [ ] Node selection/multi-selection
- [ ] Pan/zoom canvas

### Phase 3: Serialization and Export (P1)

#### 3.1 JSON Serialization
```json
{
  "version": "1.0",
  "network": {
    "nodes": [
      {
        "id": "node_001",
        "type": "AddNode",
        "position": [100, 200],
        "parameters": {
          "value": 42
        }
      }
    ],
    "connectors": [
      {
        "from_node": "node_001",
        "from_output": "result",
        "to_node": "node_002",
        "to_input": "input1"
      }
    ]
  }
}
```

#### 3.2 Python Export
```python
# Auto-generated Python code
def generated_network():
    # Node: node_001 (AddNode)
    node_001_result = add_function(input1=10, input2=20)

    # Node: node_002 (MultiplyNode)
    node_002_result = multiply_function(
        input1=node_001_result,
        multiplier=2.0
    )

    return node_002_result
```

### Phase 4: Advanced Features (P2 - Secondary Priority)

- [ ] Undo/Redo system
- [ ] Horizontal layout optimization
- [ ] Node search/filtering
- [ ] Keyboard shortcut system
- [ ] Theme/styling system

---

## Houdini-Style Naming Convention

### Terminology Mapping

| Concept | Houdini Term | This Project |
|---------|-------------|--------------|
| Node Graph | Network | `Network` |
| Node | Node | `Node` |
| Input/Output | Connector | `Connector` / `Port` |
| Parameter | Parameter / Parm | `Parameter` |
| Subnetwork | Subnet | `Subnet` |
| Execution | Cook | `cook()` / `evaluate()` |
| Parameter Panel | Parameters Pane | `ParametersPane` |

### Class Naming Convention
- Model classes: `XxxModel` (e.g., `NodeModel`)
- View classes: `XxxView` / `XxxItem` (e.g., `NetworkView`, `NodeGraphicsItem`)
- Widget classes: `XxxPane` / `XxxWidget` (e.g., `ParametersPane`)
- Node classes: `XxxNode` (e.g., `PythonNode`)

---

## Integration Interface with node-graph-core

### Interface Definition (Future Migration)

```python
# In nodegraph/core/interfaces.py

class IExecutionEngine(ABC):
    """Execution engine interface - to be implemented by node-graph-core"""

    @abstractmethod
    def evaluate_network(self, network_model: 'NetworkModel') -> dict:
        """Evaluate entire network"""
        pass

    @abstractmethod
    def cook_node(self, node_model: 'NodeModel') -> Any:
        """Execute single node"""
        pass

class IPythonExporter(ABC):
    """Python export interface"""

    @abstractmethod
    def export_to_python(self, network_model: 'NetworkModel') -> str:
        """Export to Python code"""
        pass
```

### Plugin Loading

```python
# Future loading of node-graph-core
from nodegraph.core.interfaces import IExecutionEngine

# Use built-in implementation by default
engine = DefaultExecutionEngine()

# Or load external core
try:
    from node_graph_core import AdvancedExecutionEngine
    engine = AdvancedExecutionEngine()
except ImportError:
    pass
```

---

## Technical Details

### Data Flow Model

- **Pull-based evaluation** (lazy evaluation, like Houdini)
- Nodes only cook when needed
- Supports caching and dirty marking

### Parameter Change Propagation

```python
# Parameter change -> mark node dirty -> trigger re-cook
parameter.value_changed.connect(node.mark_dirty)
node.dirty_changed.connect(network.propagate_dirty)
```

### Undo/Redo System

- Uses Qt's `QUndoStack`
- All operations wrapped as `QUndoCommand`
- Supports macro commands (batch operations)

---

## Example Use Cases

### Use Case 1: Node-based Qt Designer

```python
# Create UI layout nodes
layout = VBoxLayoutNode()
button1 = PushButtonNode(text="Click Me")
label1 = LabelNode(text="Result")

# Connect signals
button1.output("clicked") >> label1.input("setText")
```

### Use Case 2: Data Processing Pipeline

```python
# Read data
data_source = CSVReaderNode(file_path="data.csv")

# Process data
filtered = FilterNode(condition="value > 100")
transformed = MapNode(function=lambda x: x * 2)

# Output results
output = CSVWriterNode(file_path="output.csv")

# Build pipeline
data_source >> filtered >> transformed >> output
```

---

## Next Steps

1. **Create Project Base Structure**
   - Initialize Python package
   - Configure requirements.txt
   - Setup pytest

2. **Implement Core Model Layer**
   - `NetworkModel`
   - `NodeModel`
   - `ParameterModel`

3. **Implement Base Nodes**
   - `BaseNode`
   - `PythonNode`
   - Node registry system

4. **Implement Property Panel**
   - `ParametersPane` UI
   - Parameter type system

5. **Unit Tests**
   - Model layer tests
   - Serialization tests

---

## Performance Considerations

- Rendering optimization for large networks (1000+ nodes)
- Lazy loading of subnets
- Connection line QPainterPath caching
- Viewport culling

---

## Extensibility Design

### Custom Node Packages

Users can create independent node packages:

```
my_custom_nodes/
├── __init__.py
├── nodes/
│   ├── my_node.py
│   └── another_node.py
└── package.json  # Node package metadata
```

Load custom packages:

```python
from nodegraph import NodeRegistry

registry = NodeRegistry.instance()
registry.load_package("path/to/my_custom_nodes")
```

---

## License

MIT License (Recommended)

---

## References

- QtNodes: https://github.com/paceholder/nodeeditor
- NodeGraphQt: https://github.com/jchanvfx/NodeGraphQt
- PyFlow: https://github.com/pedroCabrera/PyFlow
- Houdini Documentation: https://www.sidefx.com/docs/
