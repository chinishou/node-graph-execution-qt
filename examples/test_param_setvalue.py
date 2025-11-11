"""Test parameter set_value in detail."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from nodegraph.core.models import ParameterModel
from nodegraph.core.data_types import DataTypeRegistry

# Create a parameter
param = ParameterModel(name="test", data_type="float", default_value=1.0)

print(f"Initial value: {param.value()}, type: {type(param.value())}")
print(f"_value: {param._value}, type: {type(param._value)}")

# Test type conversion
print(f"\nTesting DataTypeRegistry.convert(2.0, 'float'):")
converted = DataTypeRegistry.convert(2.0, 'float')
print(f"  Result: {converted}, type: {type(converted)}")

# Test comparison
print(f"\n1.0 == 1.0: {1.0 == 1.0}")
print(f"1.0 != 2.0: {1.0 != 2.0}")

# Now test set_value step by step
print(f"\n--- set_value(2.0) ---")
value = 2.0
print(f"1. Input value: {value}, type: {type(value)}")

converted_value = DataTypeRegistry.convert(value, param.data_type)
print(f"2. Converted value: {converted_value}, type: {type(converted_value)}")

old_value = param._value
print(f"3. Old value: {old_value}, type: {type(old_value)}")

print(f"4. old_value != converted_value: {old_value != converted_value}")
print(f"5. Should emit: {True and (old_value != converted_value)}")

# Actually call set_value
emit_count = [0]

def callback(v):
    emit_count[0] += 1
    print(f"  >>> Callback called! Value: {v}")

param.value_changed.connect(callback)

print(f"\n6. Calling set_value(2.0)...")
param.set_value(2.0)
print(f"7. Emit count: {emit_count[0]}")
print(f"8. New value: {param.value()}")
