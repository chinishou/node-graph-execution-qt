"""
Python Exporter
===============

Export node networks as executable Python code.
"""

from typing import List, Set
from ..models import NetworkModel, NodeModel


class PythonExporter:
    """
    Export node networks as Python code.

    This allows users to generate standalone Python scripts from their networks.

    Example::

        exporter = PythonExporter()
        code = exporter.export(network)

        # Save to file
        with open("generated.py", "w") as f:
            f.write(code)
    """

    @classmethod
    def export(cls, network: NetworkModel, function_name: str = "run_network") -> str:
        """
        Export a network as Python code.

        Args:
            network: The network to export
            function_name: Name of the generated function

        Returns:
            Python code as a string
        """
        lines = []

        # Header
        lines.append('"""')
        lines.append(f'Generated from network: {network.name}')
        lines.append('"""')
        lines.append('')

        # Imports (placeholder - would analyze nodes for required imports)
        lines.append('# Imports')
        lines.append('from typing import Dict, Any')
        lines.append('')

        # Function definition
        lines.append(f'def {function_name}(inputs: Dict[str, Any] = None) -> Dict[str, Any]:')
        lines.append('    """')
        lines.append(f'    Execute the {network.name} network.')
        lines.append('    ')
        lines.append('    Args:')
        lines.append('        inputs: Dictionary of input values')
        lines.append('    ')
        lines.append('    Returns:')
        lines.append('        Dictionary of output values')
        lines.append('    """')
        lines.append('    inputs = inputs or {}')
        lines.append('')

        # Get execution order from network (uses topological sort)
        sorted_nodes = network.get_execution_order()

        if not sorted_nodes:
            lines.append('    # Empty network or cyclic graph')
            lines.append('    return {}')
        else:
            # Generate code for each node
            for node in sorted_nodes:
                lines.extend(cls._generate_node_code(node, indent='    '))
                lines.append('')

            # Collect outputs (placeholder - would need to identify output nodes)
            lines.append('    # Collect outputs')
            lines.append('    outputs = {}')
            lines.append('    # TODO: Collect final outputs from network')
            lines.append('    return outputs')

        lines.append('')

        # Main block
        lines.append('')
        lines.append('if __name__ == "__main__":')
        lines.append('    # Example usage')
        lines.append('    result = run_network()')
        lines.append('    print(result)')

        return '\n'.join(lines)

    @classmethod
    def _topological_sort(cls, network: NetworkModel) -> List[NodeModel]:
        """
        Sort nodes in topological order (for execution).

        Deprecated: Use network.get_execution_order() instead.

        Args:
            network: The network

        Returns:
            List of nodes in execution order
        """
        # Delegate to NetworkModel's implementation
        return network.get_execution_order()

    @classmethod
    def _generate_node_code(cls, node: NodeModel, indent: str = '') -> List[str]:
        """
        Generate Python code for a single node.

        Args:
            node: The node
            indent: Indentation string

        Returns:
            List of code lines
        """
        lines = []

        # Comment with node info
        lines.append(f'{indent}# Node: {node.name} ({node.node_type})')

        # Get input values
        input_names = list(node.inputs().keys())

        if input_names:
            lines.append(f'{indent}# Gather inputs')
            for input_name in input_names:
                input_conn = node.input(input_name)

                # Check if connected
                if input_conn and input_conn.is_connected():
                    # Get source node and output
                    source_conn = input_conn.connections()[0]
                    if source_conn.node:
                        source_node = source_conn.node
                        source_output = source_conn.name
                        var_name = cls._make_var_name(source_node, source_output)
                        lines.append(f'{indent}{input_name}_value = {var_name}')
                else:
                    # Use default value
                    default = input_conn.default_value if input_conn else None
                    lines.append(f'{indent}{input_name}_value = {repr(default)}')

        # Node computation (placeholder - would need node-specific logic)
        lines.append(f'{indent}# Compute')

        # Generate variable names for outputs
        output_names = list(node.outputs().keys())
        if output_names:
            output_vars = ', '.join([cls._make_var_name(node, out) for out in output_names])
            lines.append(f'{indent}# {output_vars} = compute_{node.node_type}(...)')
            lines.append(f'{indent}# TODO: Implement {node.node_type} logic')

            # Placeholder computation
            for output_name in output_names:
                var_name = cls._make_var_name(node, output_name)
                lines.append(f'{indent}{var_name} = None  # Placeholder')

        return lines

    @staticmethod
    def _make_var_name(node: NodeModel, output_name: str) -> str:
        """Create a valid Python variable name for a node output."""
        # Sanitize node name
        node_name = node.name.replace(' ', '_').replace('-', '_')

        # Remove invalid characters
        node_name = ''.join(c for c in node_name if c.isalnum() or c == '_')

        return f"{node_name}_{output_name}"
