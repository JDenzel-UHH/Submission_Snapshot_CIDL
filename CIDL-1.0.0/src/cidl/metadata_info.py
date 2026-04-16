# metadata_info.py
"""
Metadata inspection helpers for CIDL.

Provides informational utilities for dataset contexts and documentation metadata.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Any

import pandas as pd
from botocore.exceptions import ClientError

import cidl.config as config
import cidl.connection as con


# ---------------------------------------------------------------------------
# JSON cache
# ---------------------------------------------------------------------------

_JSON_CACHE: dict[str, Any] = {}


def clear_cache() -> None:
    """Clear the in-memory JSON cache.

    This is mainly useful during development or in tests where metadata should
    be reloaded explicitly.
    """
    _JSON_CACHE.clear()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _clean_root_prefix(prefix: str) -> str:
    """Normalize and validate a dataset root prefix.

    Args:
        prefix: Dataset root prefix such as ``"acic22"``.

    Returns:
        The cleaned dataset root prefix.

    Raises:
        ValueError: If the prefix is empty or path-like.
    """
    cleaned = (prefix or "").strip().strip("/")

    if not cleaned or "/" in cleaned:
        raise ValueError("prefix must be a dataset root like 'acic22' (no '/').")

    return cleaned


def _read_json(source: str, *, use_cache: bool = True) -> Any:
    """Read JSON either from a local path or from the configured S3 bucket.

    Args:
        source: Local path or object key.
        use_cache: If True, reuse previously loaded JSON objects.

    Returns:
        The parsed JSON object.
    """
    if use_cache and source in _JSON_CACHE:
        return _JSON_CACHE[source]

    path = Path(source)
    if path.exists():
        obj = json.loads(path.read_text(encoding="utf-8"))
    else:
        raw = con.bucket().Object(source).get()["Body"].read()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("utf-8-sig")
        obj = json.loads(text)

    if use_cache:
        _JSON_CACHE[source] = obj

    return obj


def _load_metadata(
    *,
    prefix: str,
    use_cache: bool = True,
) -> dict[str, Any]:
    """Load the metadata object for a dataset context.

    Args:
        prefix: Dataset root prefix.
        use_cache: If True, reuse cached JSON metadata.

    Returns:
        The parsed metadata JSON object.

    Raises:
        ValueError: If the metadata is not a top-level JSON object.
    """
    ds_root = _clean_root_prefix(prefix)
    metadata_key = config.standard_metadata_key(ds_root)
    meta = _read_json(metadata_key, use_cache=use_cache)

    if not isinstance(meta, dict):
        raise ValueError("metadata.json must be a JSON object (dict) at the top level.")

    return meta


def _join(prefix: str, name: str) -> str:
    """Join an S3 prefix and a relative object name safely."""
    return prefix.rstrip("/") + "/" + name.lstrip("/")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_datainfo(
    *,
    prefix: str | None = None,
    max_desc: int = 90,
    use_cache: bool = True,
) -> pd.DataFrame:
    """Return a tidy DataFrame for the current dataset's data dictionary.

    Resolution order:
    1) ``prefix`` argument (dataset root, e.g. ``"acic22_practice"``)
    2) ``config.get_config().prefix`` (from ``CIDL_PREFIX`` or default)

    Expected convention:
    - metadata: ``<PREFIX>/metadata/<PREFIX>_metadata.json``
    - data dictionary:
      ``meta['aux']['data_dict']`` if present,
      otherwise ``<PREFIX>/metadata/<PREFIX>_data_dict.json``

    Args:
        prefix: Optional explicit dataset root prefix.
        max_desc: Maximum width for shortened descriptions.
        use_cache: If True, reuse cached JSON metadata.

    Returns:
        A tidy pandas DataFrame with the columns
        ``name``, ``role``, ``type``, and ``description``.

    Raises:
        FileNotFoundError: If no data dictionary can be found.
    """
    ds_root = _clean_root_prefix(prefix or config.get_config().prefix)
    meta = _load_metadata(prefix=ds_root, use_cache=use_cache)

    aux = meta.get("aux") or {}
    data_dict_key = None

    if isinstance(aux, dict):
        data_dict_key = aux.get("data_dict")

    if not isinstance(data_dict_key, str) or not data_dict_key.strip():
        data_dict_key = f"{ds_root}/metadata/{ds_root}_data_dict.json"

    try:
        data_dict = _read_json(data_dict_key, use_cache=use_cache)
    except Exception as exc:
        raise FileNotFoundError(
            f"Data dictionary not found for prefix '{ds_root}'. Expected: {data_dict_key}"
        ) from exc

    if not isinstance(data_dict, dict):
        raise ValueError("data_dict.json must be a JSON object (dict) at the top level.")

    rows: list[dict[str, Any]] = []

    for variable in data_dict.get("variables", []) or []:
        if not isinstance(variable, dict):
            continue

        description = textwrap.shorten(
            str(variable.get("description", "")),
            width=max_desc,
            placeholder="…",
        )

        rows.append(
            {
                "name": variable.get("name"),
                "role": variable.get("role"),
                "type": variable.get("type"),
                "description": description,
            }
        )

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["role", "name"], na_position="last").reset_index(drop=True)

    return df


def get_available_prefixes() -> list[str]:
    """Return available dataset root prefixes in the configured bucket.

    This function inspects top-level prefixes in the bucket and keeps only those
    that satisfy the CIDL metadata convention:
    ``<PREFIX>/metadata/<PREFIX>_metadata.json``.

    Returns:
        A sorted list of available dataset root prefixes.

    Raises:
        RuntimeError: If bucket listing is not permitted or the prefix scan
            fails for another S3-related reason.
    """
    bucket_handle = con.bucket()
    client = bucket_handle.meta.client

    try:
        paginator = client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket_handle.name, Delimiter="/")
    except Exception as exc:
        raise RuntimeError(
            "Unable to initialize bucket prefix listing. "
            "Listing available dataset contexts may require ListBucket permission."
        ) from exc

    candidates: set[str] = set()

    try:
        for page in pages:
            for entry in page.get("CommonPrefixes", []):
                prefix = str(entry.get("Prefix", "")).strip().strip("/")
                if prefix:
                    candidates.add(prefix)
    except ClientError as exc:
        raise RuntimeError(
            "Failed to list available dataset prefixes in the configured bucket. "
            "This operation may require ListBucket permission."
        ) from exc

    available: list[str] = []

    for prefix in sorted(candidates):
        metadata_key = config.standard_metadata_key(prefix)
        try:
            bucket_handle.Object(metadata_key).load()
        except ClientError:
            continue
        available.append(prefix)

    return available


def get_available_datasets(
    *,
    prefix: str | None = None,
    use_cache: bool = True,
) -> pd.DataFrame:
    """Return available simulation datasets for a dataset context.

    Only simulation datasets are listed. Metadata and truth objects are not
    included.

    Resolution order:
    1) ``prefix`` argument
    2) ``config.get_config().prefix``

    Args:
        prefix: Optional explicit dataset root prefix.
        use_cache: If True, reuse cached JSON metadata.

    Returns:
        A tidy pandas DataFrame with one row per simulation dataset. The table
        includes the dataset index, filename, optional UUID, and the resolved
        simulation object key.
    """
    ds_root = _clean_root_prefix(prefix or config.get_config().prefix)
    meta = _load_metadata(prefix=ds_root, use_cache=use_cache)

    simulations_prefix = meta.get("simulations_prefix")
    if not isinstance(simulations_prefix, str) or not simulations_prefix.strip():
        raise ValueError("Metadata must contain a non-empty 'simulations_prefix' string.")

    items = meta.get("items")
    if not isinstance(items, list):
        raise ValueError("Metadata must contain an 'items' list.")

    rows: list[dict[str, Any]] = []

    for record in items:
        if not isinstance(record, dict):
            continue
        if "index" not in record:
            continue

        try:
            idx = int(record["index"])
        except Exception:
            continue

        filename = record.get("filename")
        if not isinstance(filename, str) or not filename.strip():
            continue

        rows.append(
            {
                "index": idx,
                "filename": filename,
                "uuid": record.get("uuid"),
                "simulation_key": _join(simulations_prefix, filename),
            }
        )

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("index").reset_index(drop=True)

    return df


__all__ = [
    "get_datainfo",
    "get_available_prefixes",
    "get_available_datasets",
    "clear_cache",
]