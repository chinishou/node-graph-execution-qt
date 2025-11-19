"""
Parameter Model
===============

Represents a parameter, editable properties, on a node.
"""

from pydantic import BaseModel, Field, PrivateAttr
from typing import Any, Optional, List

from ..data_types import DataTypeRegistry
from ..signals import Signal


class ParameterModel(BaseModel):
    """
    Data model for a node parameter.

    Parameters are the editable properties of a node.
    They can be integers, floats, strings, booleans, or custom types.

    Attributes:
        name: Parameter identifier
        data_type: Type of the parameter (int, float, str, bool, or custom)
        default_value: Default value
        display_name: Human-readable name
        min_value: Minimum value (for numeric types)
        max_value: Maximum value (for numeric types)
        options: List of options (for choice/enum types)
        description: Parameter description/tooltip
        value_changed: Signal emitted when value changes
    """

    name: str
    data_type: str = "float"
    default_value: Any = None
    display_name: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    options: List[Any] = Field(default_factory=list)
    description: str = ""

    # Private attributes (using PrivateAttr for Pydantic V2)
    _value: Any = PrivateAttr(default=None)
    _value_changed: Signal = PrivateAttr(default=None)

    model_config = {
        "arbitrary_types_allowed": True,  # Allow Signal type
    }

    def model_post_init(self, __context) -> None:
        """Initialize fields after Pydantic validation."""
        if self.display_name is None:
            self.display_name = self.name

        if self.default_value is not None:
            self._value = self.default_value
        else:
            # Use DataTypeRegistry to get default value for type
            self._value = DataTypeRegistry.get_default_value(self.data_type)

        self._value_changed = Signal()

    @property
    def value_changed(self) -> Signal:
        """Get value_changed signal."""
        return self._value_changed

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
        # Simple type conversion for built-in types
        converted_value = value
        if self.data_type == "int" and not isinstance(value, int):
            try:
                converted_value = int(value)
            except (ValueError, TypeError):
                converted_value = value
        elif self.data_type == "float" and not isinstance(value, float):
            try:
                converted_value = float(value)
            except (ValueError, TypeError):
                converted_value = value
        elif self.data_type == "str" and not isinstance(value, str):
            converted_value = str(value)
        elif self.data_type == "bool" and not isinstance(value, bool):
            converted_value = bool(value)

        # Clamp to min/max if applicable
        if self.min_value is not None and isinstance(converted_value, (int, float)):
            converted_value = max(self.min_value, converted_value)
        if self.max_value is not None and isinstance(converted_value, (int, float)):
            converted_value = min(self.max_value, converted_value)

        old_value = self._value
        self._value = converted_value

        if emit_signal and old_value != self._value:
            self._value_changed.emit(self._value)

    def reset_to_default(self) -> None:
        """Reset parameter to its default value."""
        self.set_value(self.default_value)

    def serialize(self) -> dict:
        """
        Serialize parameter to dictionary.

        Uses Pydantic's model_dump() with custom handling for _value.
        """
        data = self.model_dump(exclude={"value_changed"})
        data["value"] = self._value
        return data

    @classmethod
    def deserialize(cls, data: dict) -> "ParameterModel":
        """
        Deserialize parameter from dictionary.

        Args:
            data: Dictionary containing parameter data

        Returns:
            ParameterModel instance
        """
        # Extract value separately (not a model field)
        value = data.pop("value", None)

        # Create parameter using Pydantic's model_validate
        param = cls.model_validate(data)

        # Set value without emitting signal
        if value is not None:
            param.set_value(value, emit_signal=False)

        return param

    def __repr__(self) -> str:
        return f"ParameterModel(name='{self.name}', type='{self.data_type}', value={self._value})"
