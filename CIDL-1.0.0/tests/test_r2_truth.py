import cidl
from cidl.objectkey_resolution import (
    _load_metadata,
    _resolve_context,
    _resolve_dataset_key,
    _resolve_truth_key,
)


def test_r2_1_dataset_and_truth_keys_derive_from_same_metadata_record(
    require_live_s3,
    representative_indices,
):
    ds_root, metadata_key = _resolve_context(prefix="acic22")
    header, metadata = _load_metadata(
        metadata_key,
        expected_prefix=ds_root,
        use_cache=False,
        require_dataset_fields=True,
        require_truth_fields=True,
    )

    for idx in representative_indices:
        record = metadata[idx]

        dataset_key = _resolve_dataset_key(header, record)
        truth_key = _resolve_truth_key(header, record)

        assert record["index"] == idx
        assert dataset_key.endswith(record["filename"])
        assert truth_key.endswith(record["truth"])


def test_r2_2_same_selection_is_accepted_by_both_loaders(require_live_s3):
    selection = [1, 7, 25]

    datasets = cidl.load_datasets(selection)
    truth = cidl.load_truth(selection)

    assert set(datasets.keys()) == set(selection)
    assert set(truth.keys()) == set(selection)