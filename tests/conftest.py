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
    import importlib
    import os

    # Write to both stdout AND a log file for debugging
    log_file = os.path.join(os.path.dirname(__file__), 'fixture_debug.log')

    def log(msg):
        """Log to both stdout and file."""
        print(msg, flush=True)  # flush=True ensures immediate output
        with open(log_file, 'a') as f:
            f.write(msg + '\n')

    log(f"\n{'='*80}")
    log(f"[FIXTURE] reset_debug_counters BEFORE test: {request.node.name}")
    log(f"{'='*80}")

    module = None

    # Search for test_debug_signals module in sys.modules
    # It might be imported as 'test_debug_signals' or 'tests.ui.test_debug_signals'
    possible_names = [
        'tests.ui.test_debug_signals',
        'test_debug_signals',
        'ui.test_debug_signals'
    ]

    for name in possible_names:
        if name in sys.modules:
            log(f"[FIXTURE] Found module in sys.modules as: {name}")
            module = sys.modules[name]
            break

    if not module:
        # Module not found by exact name, search for any module containing 'test_debug_signals'
        log(f"[FIXTURE] Module not found by name, searching sys.modules...")
        for key in sys.modules:
            if 'test_debug_signals' in key:
                log(f"[FIXTURE] Found module by search: {key}")
                module = sys.modules[key]
                break

    if not module:
        log(f"[FIXTURE] Module not found in sys.modules (this is OK for non-UI tests)")
        log(f"[FIXTURE] Available modules with 'test': {[k for k in sys.modules.keys() if 'test' in k][:10]}")

    if module:
        count_before = sum(module.call_counts.values()) if hasattr(module, 'call_counts') else 0
        log(f"[FIXTURE] Counter value BEFORE reset: {count_before}")
        log(f"[FIXTURE] Detailed counts: {dict(module.call_counts) if hasattr(module, 'call_counts') else {}}")

        if hasattr(module, 'call_counts'):
            module.call_counts.clear()
            log(f"[FIXTURE] call_counts.clear() called")
        if hasattr(module, 'call_stack'):
            module.call_stack.clear()
            log(f"[FIXTURE] call_stack.clear() called")

        count_after_clear = sum(module.call_counts.values()) if hasattr(module, 'call_counts') else 0
        log(f"[FIXTURE] Counter value AFTER reset: {count_after_clear}")
    else:
        log(f"[FIXTURE] Module is None, skipping reset")

    log(f"{'='*80}\n")

    yield  # Run the test

    # Clear after test to prevent leaking into next test
    log(f"\n{'='*80}")
    log(f"[FIXTURE] reset_debug_counters AFTER test: {request.node.name}")
    log(f"{'='*80}")

    if 'tests.ui.test_debug_signals' in sys.modules:
        module = sys.modules['tests.ui.test_debug_signals']
        count_after = sum(module.call_counts.values()) if hasattr(module, 'call_counts') else 0
        log(f"[FIXTURE] Counter value during test: {count_after}")
        log(f"[FIXTURE] Detailed counts: {dict(module.call_counts) if hasattr(module, 'call_counts') else {}}")

        if hasattr(module, 'call_counts'):
            module.call_counts.clear()
        if hasattr(module, 'call_stack'):
            module.call_stack.clear()

        log(f"[FIXTURE] Counters cleared after test")
    else:
        log(f"[FIXTURE] Module not in sys.modules")

    log(f"{'='*80}\n")


def pytest_configure(config):
    """Configure pytest based on options."""
    if config.getoption("--show-ui"):
        # Remove offscreen platform to show actual windows
        if "QT_QPA_PLATFORM" in os.environ:
            del os.environ["QT_QPA_PLATFORM"]
