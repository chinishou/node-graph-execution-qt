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


def pytest_configure(config):
    """Configure pytest based on options."""
    if config.getoption("--show-ui"):
        # Remove offscreen platform to show actual windows
        if "QT_QPA_PLATFORM" in os.environ:
            del os.environ["QT_QPA_PLATFORM"]
