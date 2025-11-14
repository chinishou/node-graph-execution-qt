"""
Run All Tests
=============

Test runner for all test modules.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import test modules
import test_data_types
import test_variable_nodes
import test_models
import test_serialization
import test_network
import test_operators
import test_signals
import test_node_registry
import test_json_serializer
import test_python_exporter
import test_topological_execution


def main():
    """Run all test suites."""
    print("\n" + "=" * 70)
    print(" " * 20 + "NODE GRAPH EXECUTION TEST SUITE")
    print("=" * 70 + "\n")

    all_passed = True

    try:
        test_data_types.run_all_tests()
        print()
    except AssertionError as e:
        print(f"❌ DataType tests failed: {e}")
        all_passed = False

    try:
        test_variable_nodes.run_all_tests()
        print()
    except AssertionError as e:
        print(f"❌ VariableNode tests failed: {e}")
        all_passed = False

    try:
        test_models.run_all_tests()
        print()
    except AssertionError as e:
        print(f"❌ Model tests failed: {e}")
        all_passed = False

    try:
        test_serialization.run_all_tests()
        print()
    except AssertionError as e:
        print(f"❌ Serialization tests failed: {e}")
        all_passed = False

    try:
        test_network.run_all_tests()
        print()
    except AssertionError as e:
        print(f"❌ NetworkModel tests failed: {e}")
        all_passed = False

    try:
        test_operators.run_all_tests()
        print()
    except AssertionError as e:
        print(f"❌ Operator tests failed: {e}")
        all_passed = False

    try:
        test_signals.run_all_tests()
        print()
    except AssertionError as e:
        print(f"❌ Signal tests failed: {e}")
        all_passed = False

    try:
        test_node_registry.run_all_tests()
        print()
    except AssertionError as e:
        print(f"❌ NodeRegistry tests failed: {e}")
        all_passed = False

    try:
        test_json_serializer.run_all_tests()
        print()
    except AssertionError as e:
        print(f"❌ JSONSerializer tests failed: {e}")
        all_passed = False

    try:
        test_python_exporter.run_all_tests()
        print()
    except AssertionError as e:
        print(f"❌ PythonExporter tests failed: {e}")
        all_passed = False

    try:
        test_topological_execution.run_all_tests()
        print()
    except AssertionError as e:
        print(f"❌ Topological execution tests failed: {e}")
        all_passed = False

    print("=" * 70)
    if all_passed:
        print(" " * 25 + "✅ ALL TESTS PASSED")
    else:
        print(" " * 25 + "❌ SOME TESTS FAILED")
    print("=" * 70)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
