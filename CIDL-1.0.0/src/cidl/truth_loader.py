# truth_loader.py
"""
Ground-truth loading helpers for CIDL.

Loads ground-truth artifacts via the active metadata contract.
"""

from __future__ import annotations

import warnings
from io import BytesIO

import pandas as pd
from botocore.exceptions import ClientError

import cidl.connection as con
from cidl.objectkey_resolution import (
    _load_metadata,
    _resolve_context,
    _resolve_truth_key,
    _to_int_list,
    clear_metadata_cache,
)


_TRUTH_CACHE: dict[str, pd.DataFrame] = {}


def clear_truth_cache() -> None:
    """Clear cached truth DataFrames and parsed metadata."""
    _TRUTH_CACHE.clear()
    clear_metadata_cache()


def _download_truth_df(key: str, *, use_cache: bool) -> pd.DataFrame:
    """Download and read a truth parquet object from S3."""
    if use_cache and key in _TRUTH_CACHE:
        return _TRUTH_CACHE[key]

    buffer = BytesIO()
    con.bucket().Object(key).download_fileobj(buffer)
    buffer.seek(0)
    df = pd.read_parquet(buffer)

    if use_cache:
        _TRUTH_CACHE[key] = df

    return df


def load_truth(
    indices,
    *,
    prefix: str | None = None,
    use_cache: bool = True,
    strict: bool = True,
) -> dict[int, pd.DataFrame]:
    """Load one or more truth files into RAM."""
    idx_list = _to_int_list(indices)
    if not idx_list:
        return {}

    ds_root, metadata_key = _resolve_context(prefix=prefix)
    header, metadata = _load_metadata(
        metadata_key,
        expected_prefix=ds_root,
        use_cache=use_cache,
        require_truth_fields=True,
    )

    out: dict[int, pd.DataFrame] = {}
    for idx in idx_list:
        if idx not in metadata:
            raise KeyError(f"Index {idx} not found in metadata items for prefix '{ds_root}'.")

        key = _resolve_truth_key(header, metadata[idx])

        try:
            out[idx] = _download_truth_df(key, use_cache=use_cache)
        except ClientError:
            if strict:
                raise
            warnings.warn(
                f"Truth file not found for idx={idx} (key='{key}'). Skipping.",
                UserWarning,
            )

    return out


__all__ = [
    "clear_truth_cache",
    "load_truth",
]