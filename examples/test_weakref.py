"""Test weak reference behavior."""

from weakref import ref, WeakMethod

def test_function():
    print("Function called")

# Try to create weak reference to function
try:
    weak_ref = ref(test_function)
    print(f"Created weak ref: {weak_ref}")
    print(f"Dereferenced: {weak_ref()}")
except TypeError as e:
    print(f"Cannot create weak ref to function: {e}")

# Try with a method
class TestClass:
    def test_method(self):
        print("Method called")

obj = TestClass()

try:
    weak_method = WeakMethod(obj.test_method)
    print(f"Created weak method: {weak_method}")
    print(f"Dereferenced: {weak_method()}")
except TypeError as e:
    print(f"Cannot create weak method: {e}")
