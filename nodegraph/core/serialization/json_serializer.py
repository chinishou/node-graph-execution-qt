"""
JSON Serializer
===============

Save and load node networks to/from JSON files.
"""

import json
from typing import Dict, Any
from pathlib import Path
from uuid import UUID
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
    def save(cls, network: NetworkModel, file_path: str, sticky_notes: list = None, pretty: bool = True) -> bool:
        """
        Save a network to a JSON file.

        Args:
            network: The network to save
            file_path: Path to the JSON file
            sticky_notes: Optional list of sticky note items to save
            pretty: Whether to format the JSON with indentation

        Returns:
            True if save was successful
        """
        try:
            # Serialize network with sticky notes
            data = cls.serialize_network(network, sticky_notes=sticky_notes)

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
    def load(cls, file_path: str) -> tuple:
        """
        Load a network from a JSON file.

        Args:
            file_path: Path to the JSON file

        Returns:
            Tuple of (Loaded NetworkModel, sticky_notes_data list)

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

            # Deserialize network and sticky notes
            network, sticky_notes_data = cls.deserialize_network(data)

            print(f"Network loaded from: {file_path}")
            return network, sticky_notes_data

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading network: {e}")

    @classmethod
    def serialize_network(cls, network: NetworkModel, sticky_notes: list = None) -> Dict[str, Any]:
        """
        Serialize a network to a dictionary.

        Args:
            network: The network to serialize
            sticky_notes: Optional list of sticky note items to serialize

        Returns:
            Dictionary representation
        """
        data = {
            "version": cls.VERSION,
            "type": "node_graph",
            "network": network.serialize(),
        }

        # Add sticky notes if provided
        if sticky_notes is not None:
            data["sticky_notes"] = [note.to_dict() for note in sticky_notes]

        return data

    @classmethod
    def deserialize_network(cls, data: Dict[str, Any]) -> tuple:
        """
        Deserialize a network from a dictionary.

        Args:
            data: Dictionary representation

        Returns:
            Tuple of (NetworkModel instance, sticky_notes_data list)
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
                    # Convert string ID to UUID
                    node_id = node_data.get("id")
                    if isinstance(node_id, str):
                        node_id = UUID(node_id)
                    node.id = node_id
                    node.name = node_data.get("name", "Node")
                    node.set_position(*node_data.get("position", (0, 0)), emit_signal=False)

                    # Deserialize parameters
                    for param_name, param_data in node_data.get("parameters", {}).items():
                        param = node.parameter(param_name)
                        if param:
                            param.set_value(param_data.get("value"), emit_signal=False)

                    # Special handling for SubnetNode
                    if node_type == "SubnetNode" and "internal_network" in node_data:
                        # Recursively deserialize internal network
                        internal_data = {"network": node_data["internal_network"]}
                        internal_network, _ = cls.deserialize_network(internal_data)
                        node.set_internal_network(internal_network)

                    network.add_node(node)
                    node_map[node.id] = node
                else:
                    print(f"Warning: Node type '{node_type}' not registered, skipping")

            except Exception as e:
                print(f"Error deserializing node {node_data.get('name', 'unknown')}: {e}")

        # Deserialize connections
        for conn_data in network_data.get("connections", []):
            try:
                # Convert string IDs to UUIDs
                source_id = conn_data["source_node"]
                target_id = conn_data["target_node"]
                if isinstance(source_id, str):
                    source_id = UUID(source_id)
                if isinstance(target_id, str):
                    target_id = UUID(target_id)

                network.connect(
                    source_node_id=source_id,
                    source_output=conn_data["source_output"],
                    target_node_id=target_id,
                    target_input=conn_data["target_input"],
                )
            except Exception as e:
                print(f"Error deserializing connection: {e}")

        # Get sticky notes data
        sticky_notes_data = data.get("sticky_notes", [])

        return network, sticky_notes_data

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
    def from_json_string(cls, json_string: str) -> tuple:
        """
        Create network from JSON string.

        Args:
            json_string: JSON string

        Returns:
            Tuple of (NetworkModel instance, sticky_notes_data list)
        """
        data = json.loads(json_string)
        return cls.deserialize_network(data)
