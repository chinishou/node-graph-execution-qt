"""
Pytest configuration for node-graph-execution-qt tests.
"""
import os
import sys
import pytest

# Allow showing UI for debugging with environment variable
# Set SHOW_UI=1 to see the actual Qt windows during testing
if not os.environ.get("SHOW_UI"):
    # Set Qt platform to offscreen for headless testing
    os.environ["QT_QPA_PLATFORM"] = "offscreen"


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--show-ui",
        action="store_true",
        default=False,
        help="Show UI windows during tests (useful for debugging)"
    )
    parser.addoption(
        "--ui-delay",
        action="store",
        default="500",
        help="Delay in milliseconds between UI operations when --show-ui is enabled (default: 500)"
    )


@pytest.fixture(scope="session")
def show_ui(request):
    """Fixture to check if UI should be shown."""
    return request.config.getoption("--show-ui") or os.environ.get("SHOW_UI")


@pytest.fixture(scope="session")
def ui_delay(request):
    """Fixture to get UI delay in milliseconds."""
    return int(request.config.getoption("--ui-delay"))


@pytest.fixture(autouse=True, scope="function")
def reset_debug_counters(request):
    """
    Reset debug call counters before each test function.

    This prevents call_counts from accumulating across tests when running
    the full test suite (pytest tests/ui/), ensuring accurate per-test
    measurement of optimization effectiveness.

    IMPORTANT: This fixture forcibly imports test_debug_signals to ensure
    counters exist and are reset, regardless of test execution order.
    """
    import sys

    # Force import test_debug_signals to ensure counters exist
    # Use importlib to avoid issues if module is already loaded
    try:
        if 'tests.ui.test_debug_signals' in sys.modules:
            module = sys.modules['tests.ui.test_debug_signals']
        else:
            import importlib
            try:
                module = importlib.import_module('tests.ui.test_debug_signals')
            except ImportError:
                # Module doesn't exist (not running UI tests)
                module = None

        if module:
            count_before = sum(module.call_counts.values()) if hasattr(module, 'call_counts') else 0

            if hasattr(module, 'call_counts'):
                module.call_counts.clear()
            if hasattr(module, 'call_stack'):
                module.call_stack.clear()

            # Debug output to verify fixture is working
            print(f"\n[DEBUG] Reset counters before {request.node.name} (was: {count_before}, now: 0)")
    except Exception as e:
        # Catch any import errors silently for non-UI tests
        print(f"[DEBUG] Could not reset counters: {e}")

    yield  # Run the test

    # Clear after test to prevent leaking into next test
    try:
        if 'tests.ui.test_debug_signals' in sys.modules:
            module = sys.modules['tests.ui.test_debug_signals']
            count_after = sum(module.call_counts.values()) if hasattr(module, 'call_counts') else 0

            if hasattr(module, 'call_counts'):
                module.call_counts.clear()
            if hasattr(module, 'call_stack'):
                module.call_stack.clear()

            # Debug output to verify counter was used
            print(f"[DEBUG] Reset counters after {request.node.name} (was: {count_after}, now: 0)")
    except Exception:
        pass


def pytest_configure(config):
    """Configure pytest based on options."""
    if config.getoption("--show-ui"):
        # Remove offscreen platform to show actual windows
        if "QT_QPA_PLATFORM" in os.environ:
            del os.environ["QT_QPA_PLATFORM"]
