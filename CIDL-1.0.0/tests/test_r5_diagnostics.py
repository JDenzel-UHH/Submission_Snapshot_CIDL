from pathlib import Path
import json
import pytest
from botocore.exceptions import ClientError
import cidl
import cidl.connection as con
from cidl.objectkey_resolution import _load_metadata


def _store_and_check(exc_info, filename, *expected_parts):
    msg = str(exc_info.value)

    out_dir = Path(__file__).resolve().parent / "outputs" / "test_r5_1_messages"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / filename).write_text(
        f"{type(exc_info.value).__name__}\n{msg}\n",
        encoding="utf-8",
    )

    for part in expected_parts:
        assert part in msg



def test_r5_1_invalid_endpoint_is_reported(monkeypatch):
    monkeypatch.setenv("CIDL_S3_ENDPOINT", "not-a-valid-endpoint")
    cidl.reset_connection()

    with pytest.raises(ValueError) as exc_info:
        cidl.connect_s3()

    _store_and_check(exc_info, "invalid_endpoint.txt", "CIDL_S3_ENDPOINT", "not-a-valid-endpoint")


def test_r5_1_missing_profile_is_reported(monkeypatch):
    monkeypatch.setenv("CIDL_AWS_PROFILE", "definitely-not-a-real-profile")
    monkeypatch.setenv("CIDL_S3_ENDPOINT", "primary")
    cidl.reset_connection()

    with pytest.raises(RuntimeError) as exc_info:
        cidl.connect_s3()

    _store_and_check(exc_info, "missing_profile.txt", "AWS profile")


def test_r5_1_metadata_contract_violation_is_reported(tmp_path):
    bad_meta = {
        "schema_version": 1,
        "prefix": "acic22",
        "items": [{"index": 1, "filename": "sim_0001.parquet", "uuid": "x"}],
    }

    path = tmp_path / "bad_metadata.json"
    path.write_text(json.dumps(bad_meta), encoding="utf-8")

    with pytest.raises(ValueError) as exc_info:
        _load_metadata(
            str(path),
            expected_prefix="acic22",
            use_cache=False,
            require_dataset_fields=True,
        )

    _store_and_check(exc_info, "metadata_contract_violation.txt", "simulations_prefix")


def test_r5_1_missing_object_is_propagated(tmp_path):
    with pytest.raises(ClientError) as exc_info:
        cidl.download_key(
            "acic22/simulations/this_object_does_not_exist.parquet",
            tmp_path / "missing.parquet",
        )

    _store_and_check(exc_info, "missing_object.txt", "HeadObject", "Not Found")


def test_r5_1_invalid_credentials_are_reported(monkeypatch):
    monkeypatch.setenv("CIDL_AWS_PROFILE", "cidl-test-wrong")
    monkeypatch.setenv("CIDL_S3_ENDPOINT", "primary")
    cidl.reset_connection()


    with pytest.raises(RuntimeError) as exc_info:
        cidl.healthcheck()

    _store_and_check(
        exc_info,
        "invalid_secret_key.txt",
        "S3 healthcheck failed",
        "profile='cidl-test-wrong'",
    )



def test_r5_1_permission_error_is_reported(monkeypatch, tmp_path):
    class FakeObject:
        def download_file(self, destination):
            raise ClientError(
                {
                    "Error": {
                        "Code": "AccessDenied",
                        "Message": "Access Denied",
                    }
                },
                "GetObject",
            )

    class FakeBucket:
        def Object(self, key):
            return FakeObject()

    monkeypatch.setattr(con, "bucket", lambda: FakeBucket())

    with pytest.raises(ClientError) as exc_info:
        cidl.download_key(
            "acic22/simulations/sim_0001.parquet",
            tmp_path / "forbidden.parquet",
        )

    _store_and_check(
        exc_info,
        "permission_error.txt",
        "AccessDenied",
        "GetObject",
    )

