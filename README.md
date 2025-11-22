# Node Graph Execution Qt

Houdini-style node-based programming framework built with PySide6/PyQt6.

## Features

- **Horizontal Layout** - Houdini-style node network editor
- **Property Panel** - Real-time node parameter editing with automatic type conversion
- **Subnet Nodes** - Support for modularization and encapsulation with recursive type resolution
- **Python Nodes** - Write Python code directly in nodes
- **Custom Nodes** - Simple API for creating your own nodes with polymorphic design
- **JSON Serialization** - Save and load node networks with complete state preservation
- **Python Export** - Export node networks as pure Python scripts
- **Undo/Redo** - Complete operation history
- **Polymorphic Type System** - Extensible type resolution without hardcoded checks
- **Automatic Type Conversion** - Smart conversion for connector default values

## Use Cases

1. **Node-based Qt Designer** - Visually build Qt UI
2. **Rapid Prototyping** - Junior developers quickly understand and modify through nodes
3. **Code Reuse** - Encapsulate common functions as nodes, maximize reusability
4. **Senior Developer Optimization** - Focus on underlying node implementation, provide high-quality components
5. **Data Processing Pipelines** - Visual data flow with type safety and automatic conversion

## Installation

### From source (local development)

```bash
# Clone the repository
git clone https://github.com/yourusername/node-graph-execution-qt.git
cd node-graph-execution-qt

# Install in editable mode (core only)
pip install -e .

# Install with Qt GUI support
pip install -e ".[qt]"

# Install with all dependencies (dev + docs)
pip install -e ".[all]"
```

### From PyPI (coming soon)

```bash
pip install node-graph-execution-qt
```

## Quick Start

### Core Usage (without Qt)

```python
from nodegraph import NetworkModel, NodeRegistry
from nodegraph.nodes.operators import AddNode

# Register and create nodes
NodeRegistry.register(AddNode)
network = NetworkModel("My Network")

# Create and configure node
node = NodeRegistry.create_node("AddNode")
node.input("a").default_value = 10.0
node.input("b").default_value = 20.0
network.add_node(node)

# Execute
node.cook()
print(node.get_output_value("result"))  # 30.0
```

### With Qt GUI (requires `[qt]` extra)

```python
from nodegraph import NetworkEditor
from qtpy.QtWidgets import QApplication

app = QApplication([])
editor = NetworkEditor()
editor.show()
app.exec()
```

## Creating Custom Nodes

```python
from nodegraph.nodes.base import BaseNode
from nodegraph.parameters import FloatParameter

class AddNode(BaseNode):
    """Addition node"""

    category = "Math"

    def __init__(self):
        super().__init__()
        self.add_input("a", data_type="float")
        self.add_input("b", data_type="float")
        self.add_output("result", data_type="float")

    def compute(self, **inputs):
        a = inputs.get("a", 0.0)
        b = inputs.get("b", 0.0)
        return {"result": a + b}
```

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for details.

## Development Status

Current Version: **0.2.0-beta**

- [x] Architecture design
- [x] Core Model layer
- [x] View layer implementation
- [x] Property panel with automatic type conversion
- [x] Custom node system with polymorphic design
- [x] JSON serialization with connector default values
- [x] Python export
- [x] SubnetNode with recursive type resolution
- [x] Automatic type conversion system
- [x] Qt-based visual editor
- [x] Node palette with Tab/Right-click
- [x] Connection visualization with Bezier curves
- [x] Output display panel

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture and design patterns
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Developer documentation for extending the system
- [USER_GUIDE.md](USER_GUIDE.md) - User manual for using the node editor
- [@forLLM@/](for LLM@/) - Context documentation for AI assistants

## License

MIT License

## Reference Projects

- [QtNodes](https://github.com/paceholder/nodeeditor)
- [NodeGraphQt](https://github.com/jchanvfx/NodeGraphQt)
- [PyFlow](https://github.com/pedroCabrera/PyFlow)
- [Nodezator](https://github.com/IndieSmiths/nodezator)
