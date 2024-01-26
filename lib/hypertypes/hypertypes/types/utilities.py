"""Utility functions for the pypechain generated files.

DO NOT EDIT.  This file was generated by pypechain.  See documentation at
https://github.com/delvtech/pypechain"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any, Tuple, TypeVar, cast

T = TypeVar("T")


def tuple_to_dataclass(cls: type[T], structs: dict[str, Any], tuple_data: Any | Tuple[Any, ...]) -> T:
    """
    Converts a tuple (including nested tuples) to a dataclass instance.  If cls is not a dataclass,
    then the data will just be passed through this function.

    Parameters
    ----------
    cls: type[T]
        The dataclass type to which the tuple data is to be converted.
    tuple_data: Any | Tuple[Any, ...]
        A tuple (or nested tuple) of values to convert into a dataclass instance.

    Returns
    -------
    T
        Either an instance of cls populated with data from tuple_data or tuple_data itself.
    """
    if not is_dataclass(cls):
        return cast(T, tuple_data)

    field_types = {field.name: field.type for field in fields(cls)}
    field_values = {}

    for (field_name, field_type), value in zip(field_types.items(), tuple_data):
        field_type = structs.get(field_type, field_type)
        if is_dataclass(field_type):
            # Recursively convert nested tuples to nested dataclasses
            field_values[field_name] = tuple_to_dataclass(field_type, structs, value)
        elif isinstance(value, tuple) and not getattr(field_type, "_name", None) == "Tuple":
            # If it's a tuple and the field is not intended to be a tuple, assume it's a nested dataclass
            field_values[field_name] = tuple_to_dataclass(field_type, structs, value)
        else:
            # Otherwise, set the primitive value directly
            field_values[field_name] = value

    return cls(**field_values)


def dataclass_to_tuple(instance: Any) -> Any:
    """Convert a dataclass instance to a tuple, handling nested dataclasses.
    If the input is not a dataclass, return the original value.

    Parameters
    ----------
    instance : Any
        The dataclass instance to convert to a tuple.  If it is not it passes through.

    Returns
    -------
    Any
        either a tuple or the orginial value
    """
    if not is_dataclass(instance):
        return instance

    def convert_value(value: Any) -> Any:
        """Convert nested dataclasses to tuples recursively, or return the original value."""
        if is_dataclass(value):
            return dataclass_to_tuple(value)
        return value

    return tuple(convert_value(getattr(instance, field.name)) for field in fields(instance))


def rename_returned_types(
    structs: dict[str, Any], return_types: list[Any] | Any, raw_values: list[str | int | tuple] | str | int | tuple
) -> tuple:
    """Convert structs in the return value to known dataclasses.

    Parameters
    ----------
    return_types : list[str] | str
        The type or list of types returned from a contract.
    raw_values : list[str  |  int | tuple] | str | int | tuple
        The actual returned values from the contract.

    Returns
    -------
    tuple
        The return types.
    """
    # cover case of multiple return values
    if isinstance(return_types, list):
        # Ensure raw_values is a tuple for consistency
        if not isinstance(raw_values, list):
            raw_values = (raw_values,)

        # Convert the tuple to the dataclass instance using the utility function
        converted_values = tuple(
            tuple_to_dataclass(return_type, structs, value) for return_type, value in zip(return_types, raw_values)
        )

        return converted_values

    # cover case of single return value
    converted_value = tuple_to_dataclass(return_types, structs, raw_values)
    return converted_value
