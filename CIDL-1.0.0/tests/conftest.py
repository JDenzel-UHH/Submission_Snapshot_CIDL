import pytest
import cidl
from botocore.exceptions import EndpointConnectionError, ClientError


@pytest.fixture(autouse=True)
def clean_cidl_state():
    cidl.reset_connection()
    cidl.reset_config()
    cidl.clear_metadata_cache()
    cidl.clear_truth_cache()
    cidl.clear_index_cache()
    cidl.clear_metadata_info_cache()
    yield
    cidl.reset_connection()
    cidl.reset_config()
    cidl.clear_metadata_cache()
    cidl.clear_truth_cache()
    cidl.clear_index_cache()
    cidl.clear_metadata_info_cache()


@pytest.fixture(scope="module")
def require_live_s3():
    try:
        cidl.healthcheck()
    except (EndpointConnectionError, RuntimeError, ClientError, ValueError) as exc:
        pytest.skip(f"Live S3 environment not available or not configured correctly: {exc}")


@pytest.fixture
def representative_indices():
    return [1, 1700, 3400]