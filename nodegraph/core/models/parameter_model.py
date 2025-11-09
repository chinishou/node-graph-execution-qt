"""
Parameter Model
===============

Represents a parameter (parm in Houdini terminology) on a node.
Parameters are editable properties that control node behavior.
"""

from typing import Any, Optional, Dict
from ..signals import Signal


class ParameterModel:
    """
    Data model for a node parameter.

    Parameters are the editable properties of a node, similar to Houdini's parms.
    They can be integers, floats, strings, colors, etc.

    Attributes:
        name: Parameter identifier
        display_name: Human-readable name
        value: Current parameter value
        default_value: Default value
        data_type: Type of the parameter (int, float, string, etc.)
        min_value: Minimum value (for numeric types)
        max_value: Maximum value (for numeric types)
        options: List of options (for choice/enum types)
        description: Parameter description/tooltip
        value_changed: Signal emitted when value changes
    """

    def __init__(
        self,
        name: str,
        data_type: str = "float",
        default_value: Any = None,
        display_name: Optional[str] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        options: Optional[list] = None,
        description: str = "",
    ):
        self.name = name
        self.data_type = data_type
        self.default_value = default_value
        self.display_name = display_name or name
        self.min_value = min_value
        self.max_value = max_value
        self.options = options or []
        self.description = description

        # Initialize value
        self._value = default_value if default_value is not None else self._get_default_for_type()

        # Signals
        self.value_changed = Signal()

    def _get_default_for_type(self) -> Any:
        """Get default value based on data type."""
        defaults = {
            "int": 0,
            "float": 0.0,
            "string": "",
            "bool": False,
            "color": (1.0, 1.0, 1.0, 1.0),  # RGBA
        }
        return defaults.get(self.data_type, None)

    def value(self) -> Any:
        """Get current parameter value."""
        return self._value

    def set_value(self, value: Any, emit_signal: bool = True) -> None:
        """
        Set parameter value.

        Args:
            value: New value
            emit_signal: Whether to emit value_changed signal
        """
        # Type conversion
        converted_value = self._convert_value(value)

        # Clamp to min/max if applicable
        if self.min_value is not None and isinstance(converted_value, (int, float)):
            converted_value = max(self.min_value, converted_value)
        if self.max_value is not None and isinstance(converted_value, (int, float)):
            converted_value = min(self.max_value, converted_value)

        # Update value
        old_value = self._value
        self._value = converted_value

        # Emit signal if value actually changed
        if emit_signal and old_value != self._value:
            self.value_changed.emit(self._value)

    def _convert_value(self, value: Any) -> Any:
        """Convert value to the appropriate type."""
        if self.data_type == "int":
            return int(value)
        elif self.data_type == "float":
            return float(value)
        elif self.data_type == "string":
            return str(value)
        elif self.data_type == "bool":
            return bool(value)
        else:
            return value

    def reset_to_default(self) -> None:
        """Reset parameter to its default value."""
        self.set_value(self.default_value)

    def serialize(self) -> Dict[str, Any]:
        """Serialize parameter to dictionary."""
        return {
            "name": self.name,
            "data_type": self.data_type,
            "value": self._value,
            "default_value": self.default_value,
            "display_name": self.display_name,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "options": self.options,
            "description": self.description,
        }

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "ParameterModel":
        """Deserialize parameter from dictionary."""
        param = cls(
            name=data["name"],
            data_type=data.get("data_type", "float"),
            default_value=data.get("default_value"),
            display_name=data.get("display_name"),
            min_value=data.get("min_value"),
            max_value=data.get("max_value"),
            options=data.get("options"),
            description=data.get("description", ""),
        )
        param.set_value(data.get("value", param.default_value), emit_signal=False)
        return param

    def __repr__(self) -> str:
        return f"ParameterModel(name='{self.name}', type='{self.data_type}', value={self._value})"
