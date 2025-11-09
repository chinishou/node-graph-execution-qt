# Node Graph Execution Qt

Houdini-style node-based programming framework built with PySide6/PyQt6.

## Features

- **Horizontal Layout** - Houdini-style node network editor
- **Property Panel** - Real-time node parameter editing
- **Subnet Nodes** - Support for modularization and encapsulation
- **Python Nodes** - Write Python code directly in nodes
- **Custom Nodes** - Simple API for creating your own nodes
- **JSON Serialization** - Save and load node networks
- **Python Export** - Export node networks as pure Python scripts
- **Undo/Redo** - Complete operation history

## Use Cases

1. **Node-based Qt Designer** - Visually build Qt UI
2. **Rapid Prototyping** - Junior developers quickly understand and modify through nodes
3. **Code Reuse** - Encapsulate common functions as nodes, maximize reusability
4. **Senior Developer Optimization** - Focus on underlying node implementation, provide high-quality components

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

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

Current Version: **0.1.0-alpha**

- [x] Architecture design
- [x] Core Model layer
- [ ] View layer implementation
- [ ] Property panel
- [x] Custom node system
- [x] JSON serialization
- [x] Python export

## License

MIT License

## Reference Projects

- [QtNodes](https://github.com/paceholder/nodeeditor)
- [NodeGraphQt](https://github.com/jchanvfx/NodeGraphQt)
- [PyFlow](https://github.com/pedroCabrera/PyFlow)
- [Nodezator](https://github.com/IndieSmiths/nodezator)
