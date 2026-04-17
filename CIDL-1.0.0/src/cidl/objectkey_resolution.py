# objectkey_resolution.py
"""
Object-key resolution helpers for CIDL.

Resolves dataset contexts, validates metadata, and derives artifact keys from index references.
"""

from __future__ import annotations

import json
import numbers
from io import BytesIO
from pathlib import Path
from typing import Any

import cidl.config as cfg
import cidl.connection as con


_META_CACHE: dict[str, tuple[dict[str, Any], dict[int, dict[str, Any]]]] = {}


def clear_metadata_cache() -> None:
    """Clear cached parsed metadata."""
    _META_CACHE.clear()


def _to_int_list(indices) -> list[int]:
    if isinstance(indices, numbers.Integral):
        return [int(indices)]
    if isinstance(indices, (str, bytes)):
        raise TypeError("indices must be an integer or an iterable of integers, not a string.")
    return [int(index) for index in indices]


def _clean_dataset_prefix(prefix: str) -> str:
    """Normalize and validate a dataset root prefix."""
    cleaned = (prefix or "").strip().lstrip("/").rstrip("/")
    if not cleaned:
        raise ValueError("prefix must be a non-empty string.")
    if "/" in cleaned:
        raise ValueError("prefix must be a dataset root like 'acic22' (no '/').")
    return cleaned


def _resolve_context(*, prefix: str | None) -> tuple[str, str]:
    """Resolve dataset root prefix and metadata key."""
    ds_root = _clean_dataset_prefix(cfg.get_config().prefix if prefix is None else prefix)
    return ds_root, cfg.standard_metadata_key(ds_root)


def _join(prefix: str, name: str) -> str:
    """Join an S3 prefix and a relative object name safely."""
    return prefix.rstrip("/") + "/" + name.lstrip("/")


def _read_json_s3_or_local(source: str) -> Any:
    """Read JSON content from either a local path or an S3 object key."""
    path = Path(source)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))

    buffer = BytesIO()
    con.bucket().Object(source).download_fileobj(buffer)
    raw = buffer.getvalue()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("utf-8-sig")
    return json.loads(text)


def _validate_and_index_items(
    header: dict[str, Any],
    *,
    ds_root: str,
    require_dataset_fields: bool = False,
    require_truth_fields: bool = False,
) -> dict[int, dict[str, Any]]:
    """Validate metadata and build an index-to-record mapping."""
    if not isinstance(header, dict):
        raise ValueError("Metadata must be a JSON object (dict).")

    if header.get("schema_version") != 1:
        raise ValueError(f"Unsupported schema_version={header.get('schema_version')!r}. Expected 1.")

    meta_prefix = header.get("prefix")
    if not isinstance(meta_prefix, str) or not meta_prefix.strip():
        raise ValueError("Metadata must contain a non-empty 'prefix' string.")
    if meta_prefix.strip().strip("/") != ds_root:
        raise ValueError(
            f"Metadata prefix mismatch: expected prefix='{ds_root}', found prefix='{meta_prefix}'."
        )

    if require_dataset_fields:
        simulations_prefix = header.get("simulations_prefix")
        if not isinstance(simulations_prefix, str) or not simulations_prefix.strip():
            raise ValueError("Metadata must contain a non-empty 'simulations_prefix' string.")

    if require_truth_fields:
        truth_prefix = header.get("truth_prefix")
        if not isinstance(truth_prefix, str) or not truth_prefix.strip():
            raise ValueError("Metadata must contain a non-empty 'truth_prefix' string.")

    items = header.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("Metadata must contain a non-empty 'items' list.")

    out: dict[int, dict[str, Any]] = {}
    for record in items:
        if not isinstance(record, dict):
            raise ValueError("Each entry in 'items' must be a JSON object (dict).")
        if "index" not in record:
            raise ValueError("Each item must contain an 'index'.")

        try:
            idx = int(record["index"])
        except Exception:
            raise ValueError(f"Item index must be int-like, got: {record.get('index')!r}")

        if idx < 1:
            raise ValueError(f"Item index must be >= 1, got: {idx}")
        if idx in out:
            raise ValueError(f"Duplicate index in metadata items: {idx}")

        if require_dataset_fields:
            filename = record.get("filename")
            if not isinstance(filename, str) or not filename.strip():
                raise ValueError(f"Item {idx} must contain a non-empty 'filename' string.")

            uuid = record.get("uuid")
            if not isinstance(uuid, str) or not uuid.strip():
                raise ValueError(f"Item {idx} must contain a non-empty 'uuid' string.")

        truth = record.get("truth")
        if truth is not None and (not isinstance(truth, str) or not truth.strip()):
            raise ValueError(f"Item {idx} has invalid 'truth' (must be non-empty string if present).")
        if require_truth_fields and truth is None:
            raise ValueError(f"Item {idx} must contain a non-empty 'truth' string.")

        out[idx] = record

    return out



def _load_metadata(
    metadata_key: str,
    *,
    expected_prefix: str,
    use_cache: bool = True,
    require_dataset_fields: bool = False,
    require_truth_fields: bool = False,
) -> tuple[dict[str, Any], dict[int, dict[str, Any]]]:
    """Load, validate, and optionally cache metadata."""
    if use_cache and metadata_key in _META_CACHE:
        header, item_map = _META_CACHE[metadata_key]
        _validate_and_index_items(
            header,
            ds_root=expected_prefix,
            require_dataset_fields=require_dataset_fields,
            require_truth_fields=require_truth_fields,
        )
        return header, item_map

    header = _read_json_s3_or_local(metadata_key)
    if not isinstance(header, dict):
        raise ValueError("Metadata must be a JSON object (dict) at the top level.")

    item_map = _validate_and_index_items(
        header,
        ds_root=expected_prefix,
        require_dataset_fields=require_dataset_fields,
        require_truth_fields=require_truth_fields,
    )

    if use_cache:
        _META_CACHE[metadata_key] = (header, item_map)

    return header, item_map



def _resolve_dataset_key(header: dict[str, Any], record: dict[str, Any]) -> str:
    """Resolve the dataset object key for a metadata item."""
    simulations_prefix = header.get("simulations_prefix")
    if not isinstance(simulations_prefix, str) or not simulations_prefix.strip():
        raise ValueError("Metadata must contain a non-empty 'simulations_prefix' string.")

    filename = record.get("filename")
    if not isinstance(filename, str) or not filename.strip():
        idx = record.get("index")
        raise ValueError(
            f"Item {idx} must contain a non-empty 'filename' string." if idx is not None
            else "Metadata item must contain a non-empty 'filename' string."
        )

    return _join(simulations_prefix, filename)



def _resolve_truth_key(header: dict[str, Any], record: dict[str, Any]) -> str:
    """Resolve the ground-truth object key for a metadata item."""
    truth_prefix = header.get("truth_prefix")
    if not isinstance(truth_prefix, str) or not truth_prefix.strip():
        raise ValueError("Metadata must contain a non-empty 'truth_prefix' string.")

    truth = record.get("truth")
    if not isinstance(truth, str) or not truth.strip():
        idx = record.get("index")
        raise ValueError(
            f"Item {idx} must contain a non-empty 'truth' string." if idx is not None
            else "Metadata item must contain a non-empty 'truth' string."
        )

    return _join(truth_prefix, truth)


__all__ = [
    "clear_metadata_cache",
    "_load_metadata",
    "_resolve_context",
    "_resolve_dataset_key",
    "_resolve_truth_key",
    "_to_int_list",
]
