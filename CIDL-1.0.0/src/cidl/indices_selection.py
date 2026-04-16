# indices_selection.py
"""
Index selection helpers for CIDL.

Provides generic metadata-based sampling and ACIC22-specific DGP filtering.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Iterable

import cidl.connection as con
from cidl.objectkey_resolution import _resolve_context, _load_metadata


# ---------------------------------------------------------------------------
# ACIC22-only constants
# ---------------------------------------------------------------------------

_ACIC22_DGP_INFO_KEY = "acic22/metadata/acic22_dgp_info.json"

VALID_DIFFICULTY_LEVELS = {"all", "very_easy", "easy", "medium", "hard", "very_hard"}

VALID_CONFOUNDING_STRENGTH = {"none", "weak", "strong"}
VALID_CONFOUNDING_SOURCE = {"none", "A", "B"}
VALID_IMPACT_HETEROGENEITY = {"small", "large"}
VALID_IDIOSYNCRASY_IMPACTS = {"small", "large"}

VALID_ANY = {"any", "all", "*"}

MAP_CONFOUNDING_STRENGTH = {"none": "None", "weak": "Weak", "strong": "Strong"}
MAP_CONFOUNDING_SOURCE = {"none": "None", "A": "Scenario A", "B": "Scenario B"}
MAP_SIZE = {"small": "Small", "large": "Large"}


# ---------------------------------------------------------------------------
# JSON cache
# ---------------------------------------------------------------------------

_JSON_CACHE: dict[str, object] = {}


def clear_cache() -> None:
    """Clear the in-memory JSON cache.

    This is mainly useful during development or in tests where a fresh read of
    metadata or DGP information is desired.
    """
    _JSON_CACHE.clear()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _read_json(source: str, *, use_cache: bool = True) -> object:
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


def _unique_sorted_ints(values: Iterable[object]) -> list[int]:
    """Convert values to unique integers and return them in sorted order."""
    return sorted({int(value) for value in values})


def _sample(population: list[int], n: int | None, seed: int | None) -> list[int]:
    """Sample indices from a population in a reproducible way.

    Args:
        population: Available dataset indices.
        n: Number of indices to sample. If ``None``, return all.
        seed: Optional random seed.

    Returns:
        A sorted list of selected indices.

    Raises:
        ValueError: If ``n`` is invalid or exceeds the available population.
    """
    pop = sorted(set(population))

    if n is None:
        return pop
    if not isinstance(n, int) or n <= 0:
        raise ValueError("n must be a positive integer (or None for all).")
    if n > len(pop):
        raise ValueError(f"Requested n={n}, but only {len(pop)} indices are available.")

    rng = random.Random(seed)
    out = rng.sample(pop, k=n)
    out.sort()
    return out


def _validate_one(name: str, value: str, allowed: set[str]) -> None:
    """Validate a single selector argument against an allowed set."""
    if value not in allowed:
        raise ValueError(f"{name} must be one of {sorted(allowed)}. Got: {value!r}")


def _is_any(value: str) -> bool:
    """Return whether a selector value means 'no restriction'."""
    return value in VALID_ANY


def _require_acic22(prefix_root: str) -> None:
    """Ensure that an ACIC22-only selector is used with the ACIC22 prefix."""
    if prefix_root != "acic22":
        raise ValueError(
            "This selector is ACIC22-only (requires ACIC22 DGP metadata). "
            "Use select_indices(...) for generic datasets."
        )


def _load_dgp_list(*, use_cache: bool = True) -> list[dict[str, Any]]:
    """Load and validate the ACIC22 DGP information list."""
    obj = _read_json(_ACIC22_DGP_INFO_KEY, use_cache=use_cache)

    if not isinstance(obj, dict) or "dgps" not in obj or not isinstance(obj["dgps"], list):
        raise ValueError("acic22_dgp_info.json must be a dict with a list field 'dgps'.")

    return obj["dgps"]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def select_indices(
    n: int | None = 10,
    seed: int | None = None,
    *,
    prefix: str | None = None,
    use_cache: bool = True,
) -> list[int]:
    """Select dataset indices generically via the metadata contract."""
    dataset_root, metadata_key = _resolve_context(prefix=prefix)
    _, item_map = _load_metadata(
        metadata_key,
        expected_prefix=dataset_root,
        use_cache=use_cache,
    )
    indices = sorted(item_map.keys())
    return _sample(population=indices, n=n, seed=seed)





def select_indices_dgp(
    n: int | None = 10,
    seed: int | None = None,
    *,
    confounding_strength: str = "any",
    confounding_source: str = "any",
    impact_heterogeneity: str = "any",
    idiosyncrasy_impacts: str = "any",
    prefix: str | None = None,
    use_cache: bool = True,
) -> list[int]:
    """Select ACIC22 dataset indices by partial DGP knob configuration."""
    dataset_root, _ = _resolve_context(prefix=prefix)
    _require_acic22(dataset_root)

    if not _is_any(confounding_strength):
        _validate_one("confounding_strength", confounding_strength, VALID_CONFOUNDING_STRENGTH)
    if not _is_any(confounding_source):
        _validate_one("confounding_source", confounding_source, VALID_CONFOUNDING_SOURCE)
    if not _is_any(impact_heterogeneity):
        _validate_one("impact_heterogeneity", impact_heterogeneity, VALID_IMPACT_HETEROGENEITY)
    if not _is_any(idiosyncrasy_impacts):
        _validate_one("idiosyncrasy_impacts", idiosyncrasy_impacts, VALID_IDIOSYNCRASY_IMPACTS)

    cs_json = None if _is_any(confounding_strength) else MAP_CONFOUNDING_STRENGTH[confounding_strength]
    src_json = None if _is_any(confounding_source) else MAP_CONFOUNDING_SOURCE[confounding_source]
    het_json = None if _is_any(impact_heterogeneity) else MAP_SIZE[impact_heterogeneity]
    ido_json = None if _is_any(idiosyncrasy_impacts) else MAP_SIZE[idiosyncrasy_impacts]

    dgps = _load_dgp_list(use_cache=use_cache)

    eligible: list[int] = []
    for rec in dgps:
        if cs_json is not None and rec.get("confounding_strength") != cs_json:
            continue
        if src_json is not None and rec.get("confounding_source") != src_json:
            continue
        if het_json is not None and rec.get("impact_heterogeneity") != het_json:
            continue
        if ido_json is not None and rec.get("idiosyncrasy_of_impacts") != ido_json:
            continue
        eligible.extend(rec.get("dataset_ids", []))

    return _sample(_unique_sorted_ints(eligible), n=n, seed=seed)


__all__ = [
    "select_indices",
    "select_indices_dgp",
    "clear_cache",
]