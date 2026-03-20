"""Configuration loading services for validated user inputs."""

from __future__ import annotations

import asyncio
import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from aizynthfinder.schemas import PlanningRuntimeSchema

_ENV_PATTERN = re.compile(r"\$\{.+?\}")


def _expand_environment_variables(text: str) -> str:
    """Expand ``${VAR}`` placeholders in configuration text.

    Args:
        text: Raw configuration text.

    Returns:
        The configuration text with environment variables substituted.

    Raises:
        ValueError: If a referenced environment variable is not set.
    """
    for item in _ENV_PATTERN.findall(text):
        env_name = item[2:-1]
        if env_name not in os.environ:
            raise ValueError(f"'{env_name}' not in environment variables")
        text = text.replace(item, os.environ[env_name])
    return text


def validate_runtime_config(source: dict[str, Any]) -> PlanningRuntimeSchema:
    """Validate a runtime configuration payload.

    Args:
        source: The user-provided configuration dictionary.

    Returns:
        A validated schema object.

    Raises:
        AttributeError: If unsupported search or post-processing keys are provided.
        ValueError: If the configuration cannot be validated.
    """
    try:
        return PlanningRuntimeSchema.model_validate(source)
    except ValidationError as err:
        first_error = err.errors()[0]
        location = first_error.get("loc", ())
        if len(location) == 2 and location[0] == "search" and first_error.get("type") == "extra_forbidden":
            raise AttributeError(f"Could not find attribute to set: {location[1]}") from err
        if len(location) == 2 and location[0] == "post_processing" and first_error.get("type") == "extra_forbidden":
            raise AttributeError(f"Could not find attribute to set: {location[1]}") from err
        location_str = ".".join(str(part) for part in location)
        message = first_error.get("msg", str(err))
        raise ValueError(f"{location_str}: {message}" if location_str else message) from err


def load_configuration_dict(filename: str | Path) -> dict[str, Any]:
    """Load, expand, and validate a YAML configuration file.

    Args:
        filename: Path to a YAML configuration file.

    Returns:
        A validated configuration dictionary suitable for the runtime layer.
    """
    text = Path(filename).read_text(encoding="utf-8")
    expanded_text = _expand_environment_variables(text)
    loaded = yaml.load(expanded_text, Loader=yaml.SafeLoader) or {}
    return validate_runtime_config(loaded).model_dump(exclude_none=True)


async def load_configuration_dict_async(filename: str | Path) -> dict[str, Any]:
    """Asynchronously load a validated YAML configuration file.

    Args:
        filename: Path to a YAML configuration file.

    Returns:
        A validated configuration dictionary.

    Notes:
        The chemistry and search core remain synchronous. This async façade is
        useful when coordinating config/resource loading alongside other I/O.
    """
    return await asyncio.to_thread(load_configuration_dict, filename)
