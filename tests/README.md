# Test Suite Organization

This directory contains all tests for the Node Graph Execution Qt project, organized by category.

## Directory Structure

```
tests/
├── unit/                    # Unit tests for core components
│   ├── test_models.py       # Core model tests (NetworkModel, NodeModel, etc.)
│   ├── test_node_registry.py # Node registration and factory tests
│   ├── test_operators.py    # Math and logic operator node tests
│   ├── test_variable_nodes.py # Variable node tests
│   ├── test_data_types.py   # Data type system tests
│   └── test_signals.py      # Signal/slot system tests
│
├── integration/             # Integration tests between components
│   ├── test_network.py      # Network integration tests
│   ├── test_topological_execution.py # Execution order tests
│   ├── test_json_serializer.py # JSON serialization tests
│   ├── test_serialization.py # General serialization tests
│   └── test_python_exporter.py # Python code export tests
│
├── ui/                      # UI tests using pytest-qt
│   ├── test_ui.py           # Main UI component tests
│   ├── test_debug_signals.py # Signal flow debugging tests
│   └── test_cook_debug.py   # Node execution debugging tests
│
├── conftest.py              # Pytest configuration and fixtures
└── run_all_tests.py         # Script to run all tests
```

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run specific categories
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# UI tests only
pytest tests/ui/
```

### Run specific test file
```bash
pytest tests/unit/test_models.py -v
```

### Run with coverage
```bash
pytest tests/ --cov=nodegraph --cov-report=html
```

## Test Categories

### Unit Tests (`tests/unit/`)
Tests for individual components in isolation, without Qt dependencies where possible:
- **Core Models**: Test data models, parameters, connectors
- **Node Types**: Test individual node implementations
- **Type System**: Test data type conversions and validation
- **Signals**: Test signal/slot system functionality

### Integration Tests (`tests/integration/`)
Tests for interactions between multiple components:
- **Network Operations**: Test graph creation, connections, execution
- **Serialization**: Test saving/loading networks
- **Execution Order**: Test topological sorting and dependency resolution
- **Code Export**: Test Python code generation

### UI Tests (`tests/ui/`)
Tests for Qt-based UI components using pytest-qt:
- **Main Window**: Test application window and menu interactions
- **Network View**: Test node placement, connections, navigation
- **Signal Flow**: Test UI event handling and signal propagation
- **Debug Tools**: Test debugging utilities for execution and signals

## Writing Tests

### Unit Tests
Use standard pytest fixtures and assertions:
```python
def test_node_creation():
    node = AddNode()
    assert node is not None
    assert node.node_type == "AddNode"
```

### Integration Tests
Test component interactions:
```python
def test_network_execution():
    network = NetworkModel()
    node = AddNode()
    network.add_node(node)
    # Test execution...
```

### UI Tests
Use pytest-qt fixtures (`qtbot`, `qapp`):
```python
def test_node_view(qtbot):
    view = NetworkView()
    qtbot.addWidget(view)
    view.show()
    qtbot.waitExposed(view)
    # Test UI interactions...
```

## CI/CD

All tests run automatically on:
- Every push to feature branches
- Pull requests to main
- Scheduled daily builds

Tests must pass before merging to main.

## Test Guidelines

1. **Isolation**: Each test should be independent and not rely on other tests
2. **Clear Names**: Use descriptive test names that explain what is being tested
3. **Fixtures**: Use pytest fixtures for common setup/teardown
4. **Assertions**: Use clear assertion messages to help debug failures
5. **Coverage**: Aim for >80% code coverage for new features
6. **Speed**: Keep unit tests fast (<100ms each), integration tests reasonable (<1s each)

## Debugging Tests

### Run with verbose output
```bash
pytest tests/ -v
```

### Run with print statements
```bash
pytest tests/ -s
```

### Run specific test
```bash
pytest tests/unit/test_models.py::test_node_creation -v
```

### Debug in VS Code
Set breakpoints and use the "Python: Debug Tests" configuration.
