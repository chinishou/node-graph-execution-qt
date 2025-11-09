"""
Python Node
===========

A node that allows users to write custom Python code directly.
Similar to Houdini's Python SOP or Blender's Script Node.
"""

from typing import Dict, Any
from .base_node import BaseNode


class PythonNode(BaseNode):
    """
    A node that executes user-provided Python code.

    The code should define a function called 'cook' that takes
    inputs as keyword arguments and returns a dictionary of outputs.

    Example code::

        def cook(**inputs):
            a = inputs.get('a', 0)
            b = inputs.get('b', 0)
            return {'result': a + b}
    """

    category = "Scripting"
    description = "Execute custom Python code"

    def __init__(self, name: str = "Python", **kwargs):
        super().__init__(name=name, node_type="PythonNode", **kwargs)

    def setup(self) -> None:
        """Setup Python node with default interface."""
        # Add default code parameter
        default_code = '''def cook(**inputs):
    """
    Custom Python code.

    Available inputs: access via inputs.get('input_name', default_value)
    Return: dictionary of outputs, e.g., {'output': value}
    """
    # Your code here
    return {}
'''
        self.add_parameter(
            "code",
            data_type="string",
            default_value=default_code,
            display_name="Python Code",
            description="Python code to execute"
        )

        # Dynamic inputs/outputs can be added by user
        # For now, add a generic input and output
        self.add_input("input", data_type="any", default_value=None)
        self.add_output("output", data_type="any")

    def compute(self, **inputs) -> Dict[str, Any]:
        """Execute the user's Python code."""
        code = self.parameter("code").value()

        if not code:
            return {}

        # Create a safe execution environment
        exec_globals = {
            '__builtins__': __builtins__,
            'inputs': inputs,
        }
        exec_locals = {}

        try:
            # Execute the code
            exec(code, exec_globals, exec_locals)

            # Call the cook function if it exists
            if 'cook' in exec_locals:
                cook_func = exec_locals['cook']
                result = cook_func(**inputs)

                if isinstance(result, dict):
                    return result
                else:
                    # If result is not a dict, return it as 'output'
                    return {'output': result}
            else:
                print(f"Warning: No 'cook' function defined in Python node '{self.name}'")
                return {}

        except Exception as e:
            print(f"Error executing Python code in node '{self.name}': {e}")
            raise

    def add_dynamic_input(self, name: str, data_type: str = "any", default_value: Any = None):
        """Add a dynamic input to this Python node."""
        self.add_input(name, data_type=data_type, default_value=default_value)

    def add_dynamic_output(self, name: str, data_type: str = "any"):
        """Add a dynamic output to this Python node."""
        self.add_output(name, data_type=data_type)
