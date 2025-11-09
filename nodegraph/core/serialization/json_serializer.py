"""
JSON Serializer
===============

Save and load node networks to/from JSON files.
"""

import json
from typing import Dict, Any
from pathlib import Path
from ..models import NetworkModel
from ..registry import NodeRegistry


class JSONSerializer:
    """
    JSON serialization for node networks.

    This class handles saving networks to JSON files and loading them back.

    Example::

        # Save network
        serializer = JSONSerializer()
        serializer.save(network, "my_network.json")

        # Load network
        network = serializer.load("my_network.json")
    """

    VERSION = "1.0"

    @classmethod
    def save(cls, network: NetworkModel, file_path: str, pretty: bool = True) -> bool:
        """
        Save a network to a JSON file.

        Args:
            network: The network to save
            file_path: Path to the JSON file
            pretty: Whether to format the JSON with indentation

        Returns:
            True if save was successful
        """
        try:
            # Serialize network
            data = cls.serialize_network(network)

            # Write to file
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(data, f, ensure_ascii=False)

            print(f"Network saved to: {file_path}")
            return True

        except Exception as e:
            print(f"Error saving network: {e}")
            return False

    @classmethod
    def load(cls, file_path: str) -> NetworkModel:
        """
        Load a network from a JSON file.

        Args:
            file_path: Path to the JSON file

        Returns:
            Loaded NetworkModel

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate version
            version = data.get("version", "unknown")
            if version != cls.VERSION:
                print(f"Warning: File version ({version}) differs from current version ({cls.VERSION})")

            # Deserialize network
            network = cls.deserialize_network(data)

            print(f"Network loaded from: {file_path}")
            return network

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading network: {e}")

    @classmethod
    def serialize_network(cls, network: NetworkModel) -> Dict[str, Any]:
        """
        Serialize a network to a dictionary.

        Args:
            network: The network to serialize

        Returns:
            Dictionary representation
        """
        return {
            "version": cls.VERSION,
            "type": "node_graph",
            "network": network.serialize(),
        }

    @classmethod
    def deserialize_network(cls, data: Dict[str, Any]) -> NetworkModel:
        """
        Deserialize a network from a dictionary.

        Args:
            data: Dictionary representation

        Returns:
            NetworkModel instance
        """
        network_data = data.get("network", {})

        # Create network
        network = NetworkModel(name=network_data.get("name", "Network"))

        # Deserialize nodes using NodeRegistry
        node_map = {}
        for node_data in network_data.get("nodes", []):
            node_type = node_data.get("node_type", "BaseNode")

            # Try to create node using registry
            try:
                if NodeRegistry.is_registered(node_type):
                    node = NodeRegistry.create_node(node_type)

                    # Update node properties from serialized data
                    node.id = node_data.get("id")
                    node.name = node_data.get("name", "Node")
                    node.set_position(*node_data.get("position", (0, 0)), emit_signal=False)

                    # Deserialize parameters
                    for param_name, param_data in node_data.get("parameters", {}).items():
                        param = node.parameter(param_name)
                        if param:
                            param.set_value(param_data.get("value"), emit_signal=False)

                    network.add_node(node)
                    node_map[node.id] = node
                else:
                    print(f"Warning: Node type '{node_type}' not registered, skipping")

            except Exception as e:
                print(f"Error deserializing node {node_data.get('name', 'unknown')}: {e}")

        # Deserialize connections
        for conn_data in network_data.get("connections", []):
            try:
                network.connect(
                    source_node_id=conn_data["source_node"],
                    source_output=conn_data["source_output"],
                    target_node_id=conn_data["target_node"],
                    target_input=conn_data["target_input"],
                )
            except Exception as e:
                print(f"Error deserializing connection: {e}")

        return network

    @classmethod
    def to_json_string(cls, network: NetworkModel, pretty: bool = True) -> str:
        """
        Convert network to JSON string.

        Args:
            network: The network to serialize
            pretty: Whether to format with indentation

        Returns:
            JSON string
        """
        data = cls.serialize_network(network)

        if pretty:
            return json.dumps(data, indent=2, ensure_ascii=False)
        else:
            return json.dumps(data, ensure_ascii=False)

    @classmethod
    def from_json_string(cls, json_string: str) -> NetworkModel:
        """
        Create network from JSON string.

        Args:
            json_string: JSON string

        Returns:
            NetworkModel instance
        """
        data = json.loads(json_string)
        return cls.deserialize_network(data)
