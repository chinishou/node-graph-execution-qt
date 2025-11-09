# Architecture Design

## Overview

Three-layer architecture inspired by QtNodes and Ryven:

```
┌─────────────────────────────────────────┐
│     Application Layer (Future)          │
│  - NetworkEditor                         │
│  - ParametersPane                        │
│  - NodePalette                           │
└─────────────────────────────────────────┘
                  ↓↑
┌─────────────────────────────────────────┐
│     View Layer (To be implemented)      │
│  - NetworkView (QGraphicsView)          │
│  - NodeGraphicsItem                      │
│  - ConnectorGraphicsItem                 │
└─────────────────────────────────────────┘
                  ↓↑
┌─────────────────────────────────────────┐
│     Model Layer (✅ Implemented)        │
│  - NetworkModel                          │
│  - NodeModel                             │
│  - ParameterModel                        │
│  - ConnectorModel                        │
└─────────────────────────────────────────┘
                  ↓↑
┌─────────────────────────────────────────┐
│  Future: node-graph-core (Separated)    │
│  - Execution engine                      │
│  - Variable system                       │
│  - Flow evaluation                       │
└─────────────────────────────────────────┘
```

## Key Principles

### 1. Model-View Separation (like ryvencore)
- **Model Layer**: Pure Python, Qt-independent
- **View Layer**: Qt-based UI rendering
- **Headless Mode**: Run networks without GUI

### 2. Dual Flow Support (inspired by Ryven)
- **Data Flow**: Current implementation (lazy evaluation)
- **Execution Flow**: Future feature (trigger-based)

### 3. Extensibility
- **Custom Nodes**: Simple API with `setup()` and `compute()`
- **Node Registry**: Dynamic registration system
- **Plugin System**: Future support for node packages

## Core Components

### Current Implementation (Phase 1)

#### NetworkModel
- Graph data structure
- Node management
- Connection management
- Topological sorting
- Cycle detection

#### NodeModel
- Input/output/parameter management
- Cook mechanism (lazy evaluation)
- Dirty flag propagation
- State caching

#### ConnectorModel
- Type checking
- Single/multi-connection support
- Value propagation

#### ParameterModel
- Type-safe values (int, float, string, bool, color)
- Min/max constraints
- Change signals

### Future Components (Phase 2+)

#### Execution Flow System
```python
# Data connection (current)
add_node.output("result") >> multiply_node.input("a")

# Execution connection (future)
button.exec_output("clicked") >> handler.exec_input("trigger")
```

#### Variable System
```python
# Global variables with observers
network.set_variable("counter", 0)
get_var = GetVariableNode("counter")
set_var = SetVariableNode("counter")
```

#### Subnet Nodes
```python
# Nested networks
subnet = SubnetNode()
subnet.add_subnet_input("data_in")
subnet.add_subnet_output("data_out")
# Internal network has access to data_in/data_out
```

## Design Patterns

### Lazy Evaluation (Pull-based)
1. Mark node dirty on parameter/input change
2. Propagate dirty flag downstream
3. Cook only when output requested
4. Cache results until dirty again

### Signal System
- Custom implementation (not Qt signals)
- Weak references to prevent memory leaks
- Model layer stays Qt-independent

### Serialization
- **JSON**: Complete network state
- **Python Export**: Executable standalone code
- **Version Control**: Git-friendly format

## Future Architecture (Phase 3)

### Separation Strategy
```
node-graph-core/           # Pure Python core
├── models/
├── execution/
├── variables/
└── flow/

node-graph-qt/            # Qt wrapper
├── views/
├── widgets/
└── renderers/

node-graph-editor/        # Full application
└── main app
```

### Benefits
- Reusable core for multiple frontends
- Performance: Cython compilation support
- Testing: Headless unit tests
- Deployment: Core-only for servers

## Performance Considerations

### Current
- Pure Python implementation
- Suitable for <100 nodes

### Future Optimizations
- Cython compilation for hot paths
- Viewport culling in large networks
- Connection line caching
- Parallel node execution (multi-threading)

## Reference Implementations

| Feature | QtNodes | Ryven | NodeGraphQt | Our Impl |
|---------|---------|-------|-------------|----------|
| Model-View | ✅ | ✅ | ✅ | ✅ |
| Headless | ✅ | ✅ | ❌ | ✅ |
| Exec Flow | ❌ | ✅ | ❌ | 🔜 |
| Variables | ❌ | ✅ | ❌ | 🔜 |
| Core Separation | ❌ | ✅ | ❌ | 🔜 |

## Documentation

For detailed implementation information, see:
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Current status
- [README.md](README.md) - Roadmap and features
- Code docstrings - API documentation

## License

MIT License
