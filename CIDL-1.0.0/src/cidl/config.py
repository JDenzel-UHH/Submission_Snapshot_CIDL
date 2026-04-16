# config.py
"""
Configuration helpers for CIDL.

Resolves and caches the active bucket and dataset context.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


DEFAULT_BUCKET_NAME = "bwl-cidl-test"
DEFAULT_PREFIX = "acic22"

_CONFIG_CACHE: Optional["CIDLConfig"] = None


def _clean_prefix(prefix: str) -> str:
    """Normalize and validate a dataset prefix.

    Leading slashes are removed and trailing slashes are stripped so that the
    prefix can be used safely in object-key construction.

    Args:
        prefix: Raw prefix value.

    Returns:
        The cleaned prefix string.

    Raises:
        ValueError: If the resulting prefix is empty.
    """
    cleaned = (prefix or "").strip().lstrip("/")

    while cleaned.endswith("/"):
        cleaned = cleaned[:-1]

    if not cleaned:
        raise ValueError("CIDL_PREFIX must be a non-empty string (e.g., 'acic232').")

    return cleaned


def standard_metadata_key(prefix: str) -> str:
    """Construct the standard metadata key for a dataset prefix.

    Args:
        prefix: Dataset root prefix.

    Returns:
        The standard metadata object key for the given prefix.
    """
    cleaned_prefix = _clean_prefix(prefix)
    return f"{cleaned_prefix}/metadata/{cleaned_prefix}_metadata.json"


@dataclass(frozen=True)
class CIDLConfig:
    """Resolved configuration for the active CIDL dataset context."""

    bucket_name: str
    prefix: str

    @property
    def metadata_key(self) -> str:
        """Return the standard metadata key for the active prefix."""
        return standard_metadata_key(self.prefix)


def get_config(*, refresh: bool = False) -> CIDLConfig:
    """Return the resolved CIDL configuration.

    Configuration is cached after first resolution. Set ``refresh=True`` to
    force re-reading environment variables.

    Args:
        refresh: If True, ignore the cache and rebuild the configuration.

    Returns:
        A frozen ``CIDLConfig`` instance.
    """
    global _CONFIG_CACHE

    if _CONFIG_CACHE is not None and not refresh:
        return _CONFIG_CACHE

    bucket_name = (os.getenv("CIDL_BUCKET_NAME") or DEFAULT_BUCKET_NAME).strip() or DEFAULT_BUCKET_NAME
    prefix_env = os.getenv("CIDL_PREFIX") or os.getenv("CIDL_DEFAULT_PREFIX") or DEFAULT_PREFIX
    prefix = _clean_prefix(prefix_env)

    _CONFIG_CACHE = CIDLConfig(bucket_name=bucket_name, prefix=prefix)
    return _CONFIG_CACHE


def reset_config() -> None:
    """Clear the cached configuration.

    This is primarily useful in tests, where environment-dependent
    configuration may need to be reloaded between test cases.
    """
    global _CONFIG_CACHE
    _CONFIG_CACHE = None


__all__ = [
    "reset_config",
    "get_config",
]