#!/usr/bin/env python
"""
Standalone runner for debug signal test.

This allows running the test without pytest installed.
"""
import sys
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import after path setup
from PySide6.QtWidgets import QApplication

# Mock qtbot for standalone execution
class MockQtBot:
    """Mock qtbot for running tests without pytest-qt."""

    def addWidget(self, widget):
        """Add widget (no-op for standalone)."""
        pass

    def waitExposed(self, widget):
        """Wait for widget to be exposed."""
        widget.show()
        QApplication.processEvents()

    def wait(self, ms):
        """Wait for specified milliseconds."""
        import time
        time.sleep(ms / 1000.0)
        QApplication.processEvents()


def main():
    """Run the debug signal test."""
    # Create Qt application
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Import test function
    from tests.ui.test_debug_signals import test_signal_flow_with_debug_tracing

    # Create mock qtbot
    qtbot = MockQtBot()

    try:
        print("=" * 80)
        print("Running debug signal flow test...")
        print("=" * 80)

        # Run test
        test_signal_flow_with_debug_tracing(qtbot)

        print("\n" + "=" * 80)
        print("✅ Test completed successfully!")
        print("=" * 80)
        return 0

    except Exception as e:
        print("\n" + "=" * 80)
        print(f"❌ Test failed: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
