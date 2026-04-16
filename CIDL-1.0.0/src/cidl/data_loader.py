# data_loader.py
"""
Dataset loading helpers for CIDL.

Loads, iterates, or downloads simulation datasets resolved via metadata.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Iterator

import pandas as pd

import cidl.connection as con
from cidl.objectkey_resolution import (
    _load_metadata,
    _resolve_context,
    _resolve_dataset_key,
    _to_int_list,
)


def _download_fileobj(key: str) -> BytesIO:
    """Download an S3 object into an in-memory buffer."""
    buffer = BytesIO()
    con.bucket().Object(key).download_fileobj(buffer)
    buffer.seek(0)
    return buffer


def _read_parquet(buffer: BytesIO, *, columns: list[str] | None = None) -> pd.DataFrame:
    """Read a parquet file from an in-memory buffer into a DataFrame."""
    buffer.seek(0)
    return pd.read_parquet(buffer, columns=columns)


# ---------------------------------------------------------------------------
# Generic public helpers
# ---------------------------------------------------------------------------

def load_parquet_key(key: str, *, columns: list[str] | None = None) -> pd.DataFrame:
    """Load a parquet object from a full S3 key."""
    return _read_parquet(_download_fileobj(key), columns=columns)


def download_key(key: str, local_path: str | Path, *, overwrite: bool = False) -> Path:
    """Download an arbitrary S3 object by full key to a local file path."""
    destination = Path(local_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists() and not overwrite:
        return destination
    if destination.exists() and overwrite:
        destination.unlink()

    con.bucket().Object(key).download_file(str(destination))
    return destination


# ---------------------------------------------------------------------------
# Dataset API
# ---------------------------------------------------------------------------

def load_datasets(
    indices,
    *,
    prefix: str | None = None,
    use_cache_meta: bool = True,
    max_n: int = 20,
    columns: list[str] | None = None,
) -> dict[int, pd.DataFrame]:
    """Load one or more simulation datasets into RAM."""
    idx_list = _to_int_list(indices)
    if not idx_list:
        return {}

    if len(idx_list) > max_n:
        raise ValueError(
            f"Attempting to load {len(idx_list)} datasets into RAM (max_n={max_n}). "
            "Use iter_datasets(...) or increase max_n explicitly."
        )

    ds_root, metadata_key = _resolve_context(prefix=prefix)
    header, metadata = _load_metadata(
        metadata_key,
        expected_prefix=ds_root,
        use_cache=use_cache_meta,
        require_dataset_fields=True,
    )

    out: dict[int, pd.DataFrame] = {}
    for idx in idx_list:
        if idx not in metadata:
            raise KeyError(f"Index {idx} not found in metadata items for prefix '{ds_root}'.")
        key = _resolve_dataset_key(header, metadata[idx])
        out[idx] = load_parquet_key(key, columns=columns)

    return out


def iter_datasets(
    indices,
    *,
    prefix: str | None = None,
    use_cache_meta: bool = True,
    columns: list[str] | None = None,
    on_error: str = "raise",
) -> Iterator[tuple[int, pd.DataFrame]]:
    """Iterate over simulation datasets one by one."""
    if on_error not in {"raise", "skip"}:
        raise ValueError("on_error must be one of {'raise','skip'}.")

    idx_list = _to_int_list(indices)
    if not idx_list:
        return iter(())

    ds_root, metadata_key = _resolve_context(prefix=prefix)
    header, metadata = _load_metadata(
        metadata_key,
        expected_prefix=ds_root,
        use_cache=use_cache_meta,
        require_dataset_fields=True,
    )

    def _generator():
        for idx in idx_list:
            try:
                if idx not in metadata:
                    raise KeyError(f"Index {idx} not found in metadata items for prefix '{ds_root}'.")
                key = _resolve_dataset_key(header, metadata[idx])
                yield idx, load_parquet_key(key, columns=columns)
            except Exception as exc:
                if on_error == "skip":
                    print(f"[skip] idx={idx}: {exc}")
                    continue
                raise

    return _generator()


def download_datasets(
    indices,
    local_dir: str | Path,
    *,
    prefix: str | None = None,
    use_cache_meta: bool = True,
    overwrite: bool = False,
    skip_existing: bool = True,
) -> list[Path]:
    """Download one or more dataset parquet files to a local directory."""
    idx_list = _to_int_list(indices)
    if not idx_list:
        return []

    local_dir = Path(local_dir)
    local_dir.mkdir(parents=True, exist_ok=True)

    ds_root, metadata_key = _resolve_context(prefix=prefix)
    header, metadata = _load_metadata(
        metadata_key,
        expected_prefix=ds_root,
        use_cache=use_cache_meta,
        require_dataset_fields=True,
    )

    written: list[Path] = []
    for idx in idx_list:
        if idx not in metadata:
            raise KeyError(f"Index {idx} not found in metadata items for prefix '{ds_root}'.")

        record = metadata[idx]
        key = _resolve_dataset_key(header, record)
        destination = local_dir / Path(str(record["filename"])).name

        if destination.exists():
            if skip_existing and not overwrite:
                continue
            if overwrite:
                destination.unlink()

        con.bucket().Object(key).download_file(str(destination))
        written.append(destination)

    return written


__all__ = [
    "load_datasets",
    "iter_datasets",
    "download_datasets",
    "load_parquet_key",
    "download_key",
]