import importlib.metadata as md
import os
import pytest
import cidl
from cidl.config import get_config, reset_config


def test_environment_installed_distribution_version():
    assert md.version("cidl-uhh") == "0.6.0"


def test_environment_public_api_is_importable():
    assert hasattr(cidl, "load_datasets")
    assert hasattr(cidl, "load_truth")
    assert hasattr(cidl, "select_indices")
    assert hasattr(cidl, "get_config")


def test_environment_config_resolves_defaults(monkeypatch):
    monkeypatch.delenv("CIDL_PREFIX", raising=False)
    monkeypatch.delenv("CIDL_DEFAULT_PREFIX", raising=False)
    monkeypatch.delenv("CIDL_BUCKET_NAME", raising=False)

    reset_config()
    cfg = get_config()

    assert cfg.bucket_name == "bwl-cidl-test"
    assert cfg.prefix == "acic22"
    assert cfg.metadata_key == "acic22/metadata/acic22_metadata.json"


@pytest.mark.skipif(
    os.getenv("CIDL_RUN_LIVE_TESTS") != "1",
    reason="Live-S3-Umgebungstest nicht aktiviert.",
)
def test_environment_live_s3_healthcheck():
    msg = cidl.healthcheck()
    assert "S3 connection established successfully." in msg