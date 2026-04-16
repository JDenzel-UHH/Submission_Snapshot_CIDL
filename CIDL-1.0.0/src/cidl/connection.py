# connection.py
"""
S3 connection helpers for CIDL.

Provides lazy, cached read-only access to the configured bucket.
"""

from __future__ import annotations

import os
from threading import Lock
from typing import Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, ProfileNotFound


# ---------------------------------------------------------------------------
# Dataset target
# ---------------------------------------------------------------------------

_BUCKET_NAME = "bwl-cidl-test"


# ---------------------------------------------------------------------------
# Stable endpoint configuration
# ---------------------------------------------------------------------------

ENDPOINTS = {
    "primary": "https://s3-uhh.lzs.uni-hamburg.de",
    "site-1": "https://s3-uhh-s1.lzs.uni-hamburg.de",
    "site-2": "https://s3-uhh-s2.lzs.uni-hamburg.de",
    "site-3": "https://s3-uhh-s3.lzs.uni-hamburg.de",
}

_DEFAULT_ENDPOINT_KEY = "primary"
_DEFAULT_PROFILE = "cidl-readonly"
DEFAULT_HEALTHCHECK_KEY = "acic22/metadata/acic22_metadata.json"


# ---------------------------------------------------------------------------
# Cached connection state
# ---------------------------------------------------------------------------

_S3 = None
_BUCKET = None
_LOCK = Lock()


def reset_connection() -> None:
    """Reset the cached S3 connection state.

    This is primarily useful in tests, where a fresh connection setup may be
    required between test cases.
    """
    global _S3, _BUCKET
    _S3 = None
    _BUCKET = None


def _resolve_profile() -> str:
    """Resolve the AWS profile name from the environment."""
    return os.getenv("CIDL_AWS_PROFILE", _DEFAULT_PROFILE).strip() or _DEFAULT_PROFILE


def _resolve_endpoint_url() -> str:
    """Resolve the S3 endpoint URL from the environment.

    The environment variable ``CIDL_S3_ENDPOINT`` may contain either:
    - a known key from ``ENDPOINTS``, or
    - a full HTTP(S) URL.

    Raises:
        ValueError: If the environment value is neither a known endpoint key
            nor a full URL.
    """
    value = os.getenv("CIDL_S3_ENDPOINT", _DEFAULT_ENDPOINT_KEY).strip() or _DEFAULT_ENDPOINT_KEY

    if value in ENDPOINTS:
        return ENDPOINTS[value]
    if value.startswith("https://") or value.startswith("http://"):
        return value

    raise ValueError(
        f"CIDL_S3_ENDPOINT must be one of {list(ENDPOINTS.keys())} or a full URL, got: {value}"
    )


def _connect():
    """Create and cache the S3 resource and bucket handle.

    Returns:
        The cached boto3 bucket handle.

    Raises:
        RuntimeError: If the configured AWS profile cannot be found.
    """
    global _S3, _BUCKET

    profile = _resolve_profile()
    endpoint_url = _resolve_endpoint_url()

    try:
        session = boto3.session.Session(profile_name=profile)
    except ProfileNotFound as exc:
        raise RuntimeError(
            f"AWS profile '{profile}' not found. Create it in ~/.aws/credentials "
            f"(Windows: C:\\Users\\<you>\\.aws\\credentials) or set CIDL_AWS_PROFILE."
        ) from exc

    # Path-style addressing is typically safest for S3-compatible providers
    # such as Cloudian.
    s3 = session.resource(
        "s3",
        endpoint_url=endpoint_url,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )

    _S3 = s3
    _BUCKET = s3.Bucket(_BUCKET_NAME)
    return _BUCKET


def _ensure_connected():
    """Return the cached bucket handle, connecting on first use.

    Connection creation is guarded by a lock so that lazy initialization
    remains thread-safe.
    """
    global _BUCKET

    if _BUCKET is not None:
        return _BUCKET

    with _LOCK:
        if _BUCKET is None:
            _connect()
        return _BUCKET

def bucket():
    """Return the cached boto3 Bucket object.

    The connection is established lazily on first use.
    """
    return _ensure_connected()


def healthcheck(key: str = DEFAULT_HEALTHCHECK_KEY) -> str:
    """Run a fail-fast connectivity check via HeadObject.

    The check verifies read access to a specific object without requiring
    ``ListBucket`` permissions.

    Args:
        key: Object key used for the HeadObject check.

    Returns:
        A short success message describing the verified connection context.

    Raises:
        RuntimeError: If the object cannot be accessed successfully.
    """
    bucket_handle = _ensure_connected()
    profile = _resolve_profile()
    endpoint_url = _resolve_endpoint_url()

    try:
        bucket_handle.Object(key).load()
    except ClientError as exc:
        code = (exc.response.get("Error") or {}).get("Code", "Unknown")
        raise RuntimeError(
            f"S3 healthcheck failed ({code}). "
            f"profile='{profile}', endpoint='{endpoint_url}', object='s3://{_BUCKET_NAME}/{key}'."
        ) from exc

    return (
        "S3 connection established successfully. "
        f"Read access confirmed for bucket '{_BUCKET_NAME}' "
        f"via endpoint '{endpoint_url}' (profile '{profile}')."
    )


def connect_s3(*, healthcheck_key: Optional[str] = None):
    """Explicitly establish and return the cached S3 bucket connection.

    This function is mainly useful for debugging or fail-fast setup. Most
    loaders do not need to call it directly because they connect lazily.

    Args:
        healthcheck_key: Optional object key used for an immediate health check.

    Returns:
        The cached boto3 bucket handle.
    """
    bucket_handle = _ensure_connected()

    if healthcheck_key:
        healthcheck(healthcheck_key)

    return bucket_handle


__all__ = [
    "ENDPOINTS",
    "connect_s3",
    "bucket",
    "healthcheck",
    "reset_connection",
]