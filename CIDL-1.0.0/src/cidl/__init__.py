# __init__.py
"""
CIDL package interface.

Exposes the public API for connection, configuration, loading, metadata, and index selection.
"""

from __future__ import annotations

__version__ = "0.6.0"
__author__ = "Julian Denzel"


# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------

from .connection import (
    ENDPOINTS,
    bucket,
    connect_s3,
    healthcheck,
    reset_connection,
)


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------

from .data_loader import (
    download_datasets,
    download_key,
    iter_datasets,
    load_datasets,
    load_parquet_key,
)


# ---------------------------------------------------------------------------
# Truth loading
# ---------------------------------------------------------------------------

from .truth_loader import (
    load_truth,
    clear_truth_cache,
)


# ---------------------------------------------------------------------------
# Metadata and dataset information
# ---------------------------------------------------------------------------

from .metadata_info import (
    get_datainfo,
    get_available_datasets,
    get_available_prefixes,
    clear_cache as clear_metadata_info_cache,
)

from .objectkey_resolution import (
    clear_metadata_cache,
)


# ---------------------------------------------------------------------------
# Index selection
# ---------------------------------------------------------------------------

from .indices_selection import (
    select_indices,
    select_indices_dgp,
    clear_cache as clear_index_cache,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

from .config import (
    get_config,
    reset_config,
)


# ---------------------------------------------------------------------------
# Submodule access
# ---------------------------------------------------------------------------

from . import connection
from . import config
from . import data_loader
from . import indices_selection
from . import metadata_info
from . import objectkey_resolution
from . import truth_loader


__all__ = [
    # Package metadata
    "__version__",
    "__author__",

    # Connection
    "ENDPOINTS",
    "connect_s3",
    "bucket",
    "healthcheck",
    "reset_connection",

    # Dataset loading
    "load_datasets",
    "iter_datasets",
    "download_datasets",
    "load_parquet_key",
    "download_key",

    # Truth loading
    "load_truth",
    "clear_truth_cache",

    # Metadata and dataset information
    "get_datainfo",
    "get_available_prefixes",
    "get_available_datasets",
    "clear_metadata_cache",
    "clear_metadata_info_cache",

    # Index selection
    "select_indices",
    "select_indices_dgp",
    "clear_index_cache",

    # Configuration
    "get_config",
    "reset_config",

    # Submodules
    "connection",
    "config",
    "data_loader",
    "indices_selection",
    "metadata_info",
    "objectkey_resolution",
    "truth_loader",
]
