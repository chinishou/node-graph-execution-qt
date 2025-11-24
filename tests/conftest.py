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
def reset_debug_counters():
    """Reset debug call counters before each test (silent)."""
    import sys

    # Search for test_debug_signals module
    possible_names = ['ui.test_debug_signals', 'test_debug_signals', 'tests.ui.test_debug_signals']

    module = None
    for name in possible_names:
        if name in sys.modules:
            module = sys.modules[name]
            break

    # Reset counters before test
    if module:
        if hasattr(module, 'call_counts'):
            module.call_counts.clear()
        if hasattr(module, 'call_stack'):
            module.call_stack.clear()

    yield  # Run the test

    # Reset counters after test
    if module:
        if hasattr(module, 'call_counts'):
            module.call_counts.clear()
        if hasattr(module, 'call_stack'):
            module.call_stack.clear()


def pytest_configure(config):
    """Configure pytest based on options."""
    if config.getoption("--show-ui"):
        # Remove offscreen platform to show actual windows
        if "QT_QPA_PLATFORM" in os.environ:
            del os.environ["QT_QPA_PLATFORM"]
