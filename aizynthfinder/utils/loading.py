"""Utilities for loading classes or functions from string specifications."""

from __future__ import annotations

import importlib
from typing import Any


def _resolve_module_and_name(name_spec: str, default_module: str | None) -> tuple[str, str]:
    if "." in name_spec:
        return name_spec.rsplit(".", maxsplit=1)
    if default_module:
        return default_module, name_spec
    raise ValueError("Must provide default_module argument if not given in name_spec")


def load_dynamic_class(
    name_spec: str,
    default_module: str | None = None,
    exception_cls: type[Exception] = ValueError,
) -> Any:
    """Load an object from a dynamic specification.

    The specification can be either a bare object name, in which case
    ``default_module`` must be supplied, or a fully-qualified
    ``package.module.ObjectName`` reference.

    Args:
        name_spec: The object specification to resolve.
        default_module: Fallback module to use for bare object names.
        exception_cls: Exception type raised when resolution fails.

    Returns:
        The imported object.
    """
    try:
        module_name, name = _resolve_module_and_name(name_spec, default_module)
    except ValueError as err:
        raise exception_cls(str(err)) from err

    try:
        loaded_module = importlib.import_module(module_name)
    except ImportError as err:
        raise exception_cls(f"Unable to load module: {module_name}") from err

    try:
        return getattr(loaded_module, name)
    except AttributeError as err:
        raise exception_cls(f"Module ({module_name}) does not have a class called {name}") from err
