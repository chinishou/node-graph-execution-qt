# LLM Context Handover v7

**Date**: 2025-11-22
**Branch**: `claude/review-llm-context-handover-01HKwcTa17vTL2YGnx4UQPSn`
**Status**: Active Development
**Version**: 0.2.0-beta

---

## Project Overview

**Node Graph Execution Qt** is a Houdini-style visual programming framework built with PySide6/PyQt6. It provides a node-based alternative to traditional programming, enabling users to create data processing pipelines and applications through visual node graphs.

### Core Architecture

Three-layer architecture:
1. **Model Layer** (`nodegraph/core/`) - Pure Python, no Qt dependencies
2. **View Layer** (`nodegraph/views/`) - Qt graphics rendering
3. **Node Library** (`nodegraph/nodes/`) - Built-in and custom nodes

---

## Recent Major Changes (Session Summary)

### 1. Recursive Type Resolution Through SubnetNode Chains

**Commit**: `8890b33` - "Enable recursive type resolution through SubnetNode chains"

**Problem**:
```
float(1) -> subnet1(input->convert(int)->output) -> subnet2(only input node)
```
The internal input node in `subnet2` showed 'any' color instead of resolving the type from `subnet1`'s output (which should be 'int').

**Solution**:
Modified `SubnetInputNode.resolve_connector_display_type()` to recursively call the connected node's type resolution method:

```python
# File: nodegraph/nodes/subnet/subnet_io_nodes.py:133-141
if hasattr(connected_node, 'resolve_connector_display_type'):
    custom_type = connected_node.resolve_connector_display_type(
        connected_connector.name,
        True,  # is_output
        visited  # Prevents infinite recursion
    )
    if custom_type:
        return custom_type
```

**Impact**: Type information now propagates correctly through any depth of SubnetNode chains.

---

### 2. Automatic Type Conversion for Connector Default Values

**Commit**: `a9baa4a` - "Add automatic type conversion for connector default values"

**Problem**:
```python
float(1) -> Add(2nd input empty, parm=1) -> print
# Error: unsupported operand type(s) for +: 'float' and 'str'
```

When users input values in the Parameters Pane, they're stored as strings (from QLineEdit), but math operations expect numbers.

**Solution**:
Added `ConnectorModel._convert_value()` static method (195-276 lines) that automatically converts values based on `data_type`:

```python
# File: nodegraph/core/models/connector_model.py:195-276
@staticmethod
def _convert_value(value: Any, data_type: str) -> Any:
    """Convert value to appropriate type based on data_type."""
    if data_type == "int":
        return int(value)  # "3" -> 3
    elif data_type == "float":
        return float(value)  # "3.14" -> 3.14
    elif data_type == "any":
        # Intelligently convert strings to numbers
        if isinstance(value, str) and value.strip():
            try:
                if '.' not in value:
                    return int(value)
                else:
                    return float(value)
            except ValueError:
                return value  # Keep as string
    # ... (complete implementation with error handling)
```

Integrated into `get_value()` method:
```python
# File: nodegraph/core/models/connector_model.py:300
return self._convert_value(self.default_value, self.data_type)
```

**Impact**:
- ALL nodes automatically benefit (AddNode, MultiplyNode, etc.)
- No per-node modifications needed
- Fundamental fix at the Model layer

---

## Key Technical Concepts

### 1. Polymorphic Design Pattern

**Core Philosophy**: "從根本上去修改，而不是針對某我提到的節點" (Fix fundamentally, not just for specific nodes)

**Implementation**:

Two virtual methods in `BaseNode`:

```python
# File: nodegraph/nodes/base/base_node.py

def resolve_connector_display_type(
    self,
    connector_name: str,
    is_output: bool,
    visited: Optional[set] = None
) -> Optional[str]:
    """Override for custom type resolution logic.

    Returns:
        Type string ('int', 'float', etc.) or None for default behavior
    """
    return None

def transforms_data_type(self) -> bool:
    """Indicate whether this node transforms data types.

    Returns:
        True if node changes input type to different output type
    """
    return False
```

**Node Implementations**:

1. **ConvertNode**:
   ```python
   def transforms_data_type(self) -> bool:
       return True  # Don't use pass-through type logic
   ```

2. **SubnetNode**:
   ```python
   def resolve_connector_display_type(self, ...):
       # Look into internal network for type from SubnetOutputNode
       for node in self._internal_network.nodes():
           if isinstance(node, SubnetOutputNode):
               # Return type from connected internal node
   ```

3. **SubnetInputNode**:
   ```python
   def resolve_connector_display_type(self, ...):
       # Check parent subnet's external connection
       # Recursively resolve through chained subnets
   ```

**UI Layer (Before vs After)**:

```python
# BEFORE (Hardcoded - BAD):
if node_type == 'SubnetNode' and is_output:
    # Special handling
elif node_type == 'ConvertNode':
    # Special handling

# AFTER (Polymorphic - GOOD):
if self.connector.node:
    custom_type = self.connector.node.resolve_connector_display_type(...)
    if custom_type:
        return custom_type
```

**Benefits**:
- New node types don't require UI changes
- Follows Open-Closed Principle
- Each node encapsulates its own logic
- Extensible without modifying core

---

### 2. Cross-Network Boundary Communication

**Pattern**: Parent-child references for upward traversal

**Implementation**:
```python
# File: nodegraph/nodes/subnet/subnet_node.py

def _update_io_node_references(self):
    """Maintain backref to parent subnet."""
    for node in self._internal_network.nodes():
        if isinstance(node, (SubnetInputNode, SubnetOutputNode)):
            node._parent_subnet = self  # Backref for upward lookup
```

Called from:
- `_sync_connectors()` - When syncing I/O nodes
- After deserialization

**Usage**:
```python
# SubnetInputNode can access parent to fetch external values
if hasattr(self, '_parent_subnet') and self._parent_subnet:
    parent_input = self._parent_subnet.input(connector_name)
    value = parent_input.get_value()
```

---

### 3. Visitor Pattern for Cycle Prevention

**Problem**: Recursive type resolution could cause infinite loops with circular connections

**Solution**: `visited` set parameter

```python
def resolve_connector_display_type(
    self,
    connector_name: str,
    is_output: bool,
    visited: Optional[set] = None  # Track visited connectors
) -> Optional[str]:
    if visited is None:
        visited = set()

    connector_id = id(some_connector)
    if connector_id in visited:
        return None  # Cycle detected
    visited.add(connector_id)

    # Continue resolution...
```

---

## File Changes Summary

### Core Files Modified

1. **nodegraph/core/models/connector_model.py**
   - Added `_convert_value()` static method (195-276)
   - Modified `get_value()` to use automatic conversion (300)
   - **Impact**: Fundamental type conversion for all nodes

2. **nodegraph/nodes/base/base_node.py**
   - Added `resolve_connector_display_type()` abstract method
   - Added `transforms_data_type()` method
   - **Impact**: Polymorphic design foundation

3. **nodegraph/nodes/subnet/subnet_io_nodes.py**
   - Enhanced `SubnetInputNode.resolve_connector_display_type()` with recursion (133-141)
   - Added parent fetch logic in `compute()` for UI execution
   - **Impact**: Recursive type resolution and data passing

4. **nodegraph/nodes/subnet/subnet_node.py**
   - Added `_update_io_node_references()` for parent backref
   - Implemented `resolve_connector_display_type()` for internal network lookup
   - **Impact**: Cross-network type resolution

5. **nodegraph/nodes/operators/convert_node.py**
   - Implemented `transforms_data_type()` returning True
   - **Impact**: Correct type display for conversion nodes

6. **nodegraph/views/nodes/port_graphics_item.py**
   - Refactored from hardcoded type checks to polymorphic calls
   - Reduced from ~70 lines to ~5 lines for custom resolution
   - **Impact**: Extensible UI without modification

7. **nodegraph/core/serialization/json_serializer.py**
   - Added connector `default_value` deserialization (178)
   - **Impact**: Parameter values persist through save/load

---

## Code Patterns and Best Practices

### 1. Pydantic V2 Models

All models use Pydantic BaseModel:
```python
from pydantic import BaseModel, Field, PrivateAttr

class ConnectorModel(BaseModel):
    name: str
    data_type: str = "any"
    _connections: List["ConnectorModel"] = PrivateAttr(default_factory=list)

    model_config = {
        "arbitrary_types_allowed": True
    }
```

**Key Points**:
- Use `PrivateAttr` for non-serialized fields
- Set `arbitrary_types_allowed=True` for Signal and Qt types
- Override `serialize()` and `deserialize()` for custom data

### 2. Signal/Slot Pattern

```python
from nodegraph.core.signals import Signal

class NodeModel:
    _dirty_changed: Signal = PrivateAttr(default=None)

    def model_post_init(self, __context) -> None:
        self._dirty_changed = Signal()

    @property
    def dirty_changed(self) -> Signal:
        return self._dirty_changed
```

Usage:
```python
node.dirty_changed.connect(on_dirty)
node.mark_dirty()  # Emits signal
```

### 3. Type Checking with `hasattr`

For polymorphic calls:
```python
if hasattr(node, 'resolve_connector_display_type'):
    result = node.resolve_connector_display_type(...)
```

Allows graceful handling when method doesn't exist.

### 4. Optional Return Types for Extensibility

```python
def resolve_connector_display_type(...) -> Optional[str]:
    """Returns None to use default behavior."""
    return None
```

Allows base implementation to be non-intrusive.

---

## Testing Approach

### Test Structure

```python
# tests/test_type_conversion.py (created during development, then removed)

from nodegraph.core import NetworkModel
from nodegraph.nodes.base.variable_node import VariableNode
from nodegraph.nodes.operators.math_nodes import AddNode

def test_add_with_string_default():
    """Test automatic type conversion."""
    network = NetworkModel(name="test")

    float_node = VariableNode(data_type="float", name="Float1")
    float_node.parameter("value").set_value(5.0)
    network.add_node(float_node)

    add_node = AddNode()
    network.add_node(add_node)

    float_node.output("out").connect_to(add_node.input("a"))

    # Simulate UI string input
    add_node.input("b").default_value = "3"  # String

    # Execute and verify conversion
    result = add_node.execute()
    assert result is True
    assert add_node.get_output_value("result") == 8.0
```

**Test Results**: All tests passed ✓
- float + string → float (8.0)
- float * string → float (10.0)
- int mode with string → int (10)

---

## Common Issues and Solutions

### Issue 1: SubnetInputNode Returning None

**Symptom**:
```
float(1)->subnet(input->multiply(b=2 in parm)->output)->print returns None
```

**Root Cause**: `SubnetInputNode.compute()` only checked `_injected_input`, but direct UI execution doesn't use injection.

**Fix**: Added parent fetch logic:
```python
# Check for injected input first (subnet execution)
if hasattr(self, '_injected_input'):
    return {connector_name: self._injected_input}

# Try to get from parent subnet (UI execution)
if hasattr(self, '_parent_subnet') and self._parent_subnet:
    parent_input = self._parent_subnet.input(connector_name)
    if parent_input:
        value = parent_input.get_value()
        return {connector_name: value}
```

### Issue 2: INPUT Connector Accepting Multiple Connections

**Symptom**: SubnetOutputNode could have multiple input connections.

**Investigation**: Checked `ConnectorModel.connect_to()`:
```python
# Already correct - disconnects existing before new connection
if self.is_input() and len(self._connections) > 0:
    self.disconnect_all()
```

**Result**: No fix needed - already enforced at fundamental level.

### Issue 3: Connector default_value Not Persisting

**Symptom**: Math node parameter values reset to defaults after save/load.

**Fix**: Added deserialization in JSONSerializer:
```python
# Deserialize connector default values
for input_name, input_data in node_data.get("inputs", {}).items():
    connector = node.input(input_name)
    if connector and "default_value" in input_data:
        connector.default_value = input_data["default_value"]
```

---

## User Feedback and Design Decisions

### Critical User Feedback

> "這也是要從根本上去修改，而不是針對某我提到的節點"
> (Fix fundamentally, not just for specific nodes I mentioned)

This feedback led to the polymorphic design refactoring. Instead of adding more hardcoded checks in the UI layer for specific node types, we:

1. Added virtual methods to `BaseNode`
2. Let each node override for custom behavior
3. Removed all hardcoded `node_type` checks from UI

**Result**: System is now extensible without modifying core files.

### Design Principles Applied

1. **Open-Closed Principle**: Open for extension, closed for modification
2. **Single Responsibility**: Each node handles its own type resolution
3. **Don't Repeat Yourself**: Type conversion logic in one place (`_convert_value`)
4. **Polymorphism over Conditionals**: Use method overriding instead of type checking

---

## API Examples for LLMs

### Creating a Custom Node with Type Resolution

```python
from typing import Dict, Any, Optional
from nodegraph.nodes.base import BaseNode

class MyTransformNode(BaseNode):
    """Custom node that transforms data types."""

    category: str = "Custom"

    def __init__(self, **kwargs):
        super().__init__(name="Transform", node_type="MyTransformNode", **kwargs)

    def setup(self) -> None:
        self.add_parameter(
            "output_type",
            data_type="str",
            default_value="int",
            label="Output Type",
            menu_items=["int", "float", "str"]
        )
        self.add_input("value", data_type="any", default_value=0)
        self.add_output("result", data_type="any")

    def compute(self, **inputs) -> Dict[str, Any]:
        value = inputs.get("value", 0)
        output_type = self.parameter("output_type").value()

        if output_type == "int":
            result = int(value)
        elif output_type == "float":
            result = float(value)
        else:
            result = str(value)

        return {"result": result}

    # Polymorphic method 1: Custom type resolution
    def resolve_connector_display_type(
        self,
        connector_name: str,
        is_output: bool,
        visited: Optional[set] = None
    ) -> Optional[str]:
        """Output type matches parameter setting."""
        if is_output and connector_name == "result":
            return self.parameter("output_type").value()
        return None

    # Polymorphic method 2: Indicate type transformation
    def transforms_data_type(self) -> bool:
        """This node transforms types."""
        return True
```

### Using the Node

```python
from nodegraph.core import NetworkModel
from nodegraph.core.registry import NodeRegistry

# Register node
NodeRegistry.register(MyTransformNode)

# Create network
network = NetworkModel(name="test")

# Create and configure node
transform = NodeRegistry.create_node("MyTransformNode")
transform.parameter("output_type").set_value("float")
transform.input("value").default_value = "3.14"  # String from UI

network.add_node(transform)

# Execute
transform.execute()
print(transform.get_output_value("result"))  # 3.14 (float)

# Type resolution
print(transform.resolve_connector_display_type("result", True))  # "float"
```

---

## Data Structures

### NetworkModel Structure

```python
{
    "name": str,
    "_nodes": Dict[str, NodeModel],  # UUID -> NodeModel
    "_connections": List[Tuple[ConnectorModel, ConnectorModel]]
}
```

### NodeModel Structure

```python
{
    "id": str,  # UUID
    "name": str,
    "node_type": str,
    "position": Tuple[int, int],
    "_inputs": Dict[str, ConnectorModel],
    "_outputs": Dict[str, ConnectorModel],
    "_parameters": Dict[str, ParameterModel],
    "_output_cache": Dict[str, Any],
    "_is_dirty": bool
}
```

### ConnectorModel Structure

```python
{
    "name": str,
    "connector_type": ConnectorType,  # INPUT or OUTPUT
    "data_type": str,  # "int", "float", "str", "bool", "any"
    "label": str,
    "default_value": Any,
    "description": str,
    "_connections": List[ConnectorModel],
    "_cached_value": Any,
    "_is_dirty": bool
}
```

---

## Serialization Format

### Network JSON

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
      },
      "outputs": {}
    },
    "uuid-2": {
      "node_type": "SubnetNode",
      "name": "MySubnet",
      "position": [300, 200],
      "parameters": {},
      "inputs": {},
      "outputs": {},
      "internal_network": {
        "name": "MySubnet_internal",
        "nodes": { ... },
        "connections": [ ... ]
      }
    }
  },
  "connections": [
    {
      "source_node": "uuid-1",
      "source_connector": "result",
      "target_node": "uuid-2",
      "target_connector": "input1"
    }
  ]
}
```

---

## UI Layer Overview

### Qt Graphics Architecture

```
QGraphicsView (NetworkView)
    └── QGraphicsScene (NetworkScene)
            ├── NodeGraphicsItem (one per node)
            │       └── PortGraphicsItem (one per connector)
            └── ConnectionItem (one per connection)
```

### Event Flow

1. **User Action** (e.g., drag port):
   - `PortGraphicsItem.mousePressEvent()`
   - Creates temporary `ConnectionItem`

2. **Visual Update**:
   - `PortGraphicsItem.mouseMoveEvent()`
   - Updates `ConnectionItem` path

3. **Connection Complete**:
   - `PortGraphicsItem.mouseReleaseEvent()`
   - Calls `connector.connect_to(other)`
   - Model updates trigger view refresh

4. **Model Signals**:
   - `connector.connected_changed.emit()`
   - `node.dirty_changed.emit()`
   - UI subscribes and updates visuals

### Color Resolution in UI

```python
# File: nodegraph/views/nodes/port_graphics_item.py

def _get_effective_color(self, visited=None) -> QColor:
    """Get display color for connector."""

    # 1. Try polymorphic resolution
    if self.connector.node:
        custom_type = self.connector.node.resolve_connector_display_type(
            self.connector.name,
            self.is_output,
            visited
        )
        if custom_type:
            return DataTypeRegistry.get_color(custom_type)

    # 2. Try pass-through logic (for non-transforming nodes)
    if self.connector.is_input():
        if self.connector.is_connected():
            # Use connected output's type
            connected = self.connector.connections()[0]
            return self._get_color_from_connector(connected, visited)

    # 3. Default: use connector's data_type
    return DataTypeRegistry.get_color(self.connector.data_type)
```

---

## Current Status

### Completed Features

✅ Core model layer (NetworkModel, NodeModel, ConnectorModel, ParameterModel)
✅ Polymorphic type system
✅ Automatic type conversion
✅ Recursive type resolution through subnets
✅ Qt-based visual editor
✅ Node palette (Tab/Right-click)
✅ Connection visualization (Bezier curves)
✅ Parameters pane with type conversion
✅ Output display pane
✅ JSON serialization with complete state
✅ Python export
✅ SubnetNode with nested networks
✅ Built-in nodes (Math, Operators, Variables, Utils)

### Known Limitations

- No undo/redo system yet
- No copy/paste functionality
- No node groups/annotations
- Limited error reporting in UI
- No performance optimization for large networks (1000+ nodes)

### Future Enhancements

- [ ] Undo/Redo with QUndoStack
- [ ] Copy/Paste nodes
- [ ] Node search/filtering
- [ ] Performance profiling and optimization
- [ ] Custom data types beyond primitives
- [ ] Animation/timeline support
- [ ] Debugging tools (breakpoints, step execution)
- [ ] Plugin system for external nodes

---

## Git Commit History (Recent)

```
a9baa4a - Add automatic type conversion for connector default values
8890b33 - Enable recursive type resolution through SubnetNode chains
c152ddf - Generalize connector color resolution with polymorphic design
64fd035 - Fix SubnetInputNode to fetch value from parent when not injected
41f4b67 - Fix connector color resolution for SubnetInputNode and ConvertNode
```

---

## Documentation Files

### For Users
- **README.md**: Project overview, quick start
- **USER_GUIDE.md**: Comprehensive user manual with tutorials

### For Developers
- **ARCHITECTURE.md**: System architecture and design patterns
- **DEVELOPER_GUIDE.md**: API reference, custom node creation, best practices

### For LLMs
- **@forLLM@/LLM Context Handover v7.md** (this file): Complete context for AI assistants
- Previous versions (v1-v6): Historical context and evolution

---

## Important Notes for LLMs

### When Extending the System

1. **Always use polymorphism over type checking**
   - Add virtual methods to BaseNode
   - Let nodes override for custom behavior
   - Never hardcode `if node_type == ...` in UI layer

2. **Type conversion is automatic**
   - ConnectorModel handles conversion in `get_value()`
   - No need to convert in individual nodes
   - Works for all `data_type` values

3. **Subnet communication uses backrefs**
   - `_parent_subnet` attribute for upward traversal
   - `_update_io_node_references()` maintains consistency
   - Call after deserialization and sync operations

4. **Prevent infinite recursion**
   - Always use `visited` set in recursive methods
   - Check `id(obj)` before traversing
   - Return `None` when cycle detected

5. **Pydantic models require special handling**
   - Use `PrivateAttr` for runtime-only fields
   - Set `arbitrary_types_allowed=True` for non-JSON types
   - Override `serialize()`/`deserialize()` for custom data

### Common Patterns

**Adding a new node type**:
1. Create class inheriting from `BaseNode`
2. Define `setup()` method
3. Implement `compute()` method
4. Optional: Override `resolve_connector_display_type()` and/or `transforms_data_type()`
5. Register with `NodeRegistry.register()`

**Adding custom type resolution**:
1. Override `resolve_connector_display_type()` in node class
2. Return type string ("int", "float", etc.) or None
3. Use `visited` parameter to prevent cycles

**Adding new data type**:
1. Register in `DataTypeRegistry`
2. Add default value and color
3. Update `_convert_value()` if special conversion needed

---

## Conclusion

This project demonstrates a well-architected, extensible node graph system. The recent changes (recursive type resolution and automatic type conversion) were implemented following fundamental design principles rather than quick fixes.

Key takeaways:
- **Polymorphism** enables extensibility without modification
- **Type conversion** at the model layer benefits all nodes automatically
- **Recursive resolution** supports complex subnet chains
- **User feedback** drove architectural improvements

The system is ready for further development and can serve as a foundation for various visual programming applications.

---

**End of Context Handover v7**
