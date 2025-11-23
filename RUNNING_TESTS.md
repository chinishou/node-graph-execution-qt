# Running Tests

This document explains how to run tests for the Node Graph Execution Qt project.

## Prerequisites

Install the package with test dependencies:

```bash
# Install package with all dependencies (including test dependencies)
pip install -e ".[all]"

# Or install just the core package with Qt support
pip install -e ".[qt]"

# Install test dependencies separately if needed
pip install pytest pytest-qt
```

## Running Tests

### Run All Tests

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=nodegraph --cov-report=html
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# UI tests only (requires Qt)
pytest tests/ui/ -v
```

### Run Specific Test Files

```bash
# Run a specific test file
pytest tests/unit/test_models.py -v

# Run the debug signal test
pytest tests/ui/test_debug_signals.py -v
```

### Run Specific Test Functions

```bash
# Run a specific test function
pytest tests/unit/test_models.py::test_node_creation -v

# Run the signal flow debug test
pytest tests/ui/test_debug_signals.py::test_signal_flow_with_debug_tracing -v
```

## Common Issues

### ModuleNotFoundError: No module named 'nodegraph'

**Solution**: Install the package in editable mode:
```bash
pip install -e .
```

### ModuleNotFoundError: No module named 'pytest'

**Solution**: Install test dependencies:
```bash
pip install pytest pytest-qt
```

### ModuleNotFoundError: No module named 'PySide6'

**Solution**: Install Qt dependencies:
```bash
pip install -e ".[qt]"
```

### Qt platform plugin error

**Solution**: Set the platform to offscreen for headless testing:
```bash
export QT_QPA_PLATFORM=offscreen  # Linux/Mac
set QT_QPA_PLATFORM=offscreen     # Windows CMD
$env:QT_QPA_PLATFORM="offscreen"  # Windows PowerShell
pytest tests/ui/ -v
```

Note: This is already configured in `tests/conftest.py` for automatic headless testing.

## Test Organization

- `tests/unit/` - Unit tests for core components (no Qt required)
- `tests/integration/` - Integration tests between components
- `tests/ui/` - UI tests using pytest-qt (requires Qt)

## Debugging Tests

### Run with print statements

```bash
pytest tests/ -v -s
```

### Run with PDB debugger

```bash
pytest tests/ -v --pdb
```

### Run with detailed traceback

```bash
pytest tests/ -v --tb=long
```

## CI/CD

Tests run automatically on:
- Every push to feature branches
- Pull requests to main
- Scheduled daily builds

All tests must pass before merging to main.
