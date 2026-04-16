import pandas as pd
import pytest
import cidl
from cidl.objectkey_resolution import (
    _load_metadata,
    _resolve_context,
    _resolve_dataset_key,
    clear_metadata_cache,
)


VALID_SINGLE_INDICES = [1, 1700, 3400]
INVALID_SINGLE_INDICES = [0, -1, 3401]


@pytest.mark.parametrize("idx", VALID_SINGLE_INDICES)
def test_r1_1_valid_single__indices(require_live_s3, idx):
    out = cidl.load_datasets(idx)
    
    assert isinstance(out, dict)
    assert list(out.keys()) == [idx]
    assert isinstance(out[idx], pd.DataFrame)



@pytest.mark.parametrize("idx", INVALID_SINGLE_INDICES)
def test_r1_1_invalid_single_indices(require_live_s3, idx):
    with pytest.raises(KeyError):
        cidl.load_datasets(idx)
    


def test_r1_2_list_selection_normalization(require_live_s3):
    selection = [1, 7, 25]

    out = cidl.load_datasets(selection)

    assert isinstance(out, dict)
    assert list(out.keys()) == [1, 7, 25]
    assert all(isinstance(out[idx], pd.DataFrame) for idx in selection)


def test_r1_2_list_selection_normalization_invalid(require_live_s3):
    selection = [1, 7, 3401]

    with pytest.raises(KeyError):
        cidl.load_datasets(selection)



def test_r1_2_range_selection_normalization(require_live_s3):
    selection = range(1, 4)

    out = cidl.load_datasets(selection)

    assert isinstance(out, dict)
    assert list(out.keys()) == [1, 2, 3]
    assert all(isinstance(out[idx], pd.DataFrame) for idx in [1, 2, 3])


def test_r1_2_range_selection_normalization_invalid(require_live_s3):
    selection = range(-1, 3)

    with pytest.raises(KeyError):
        cidl.load_datasets(selection)


def test_r1_3_dataset_key_resolution_is_stable(require_live_s3):
    indices = [1, 1700, 3400]
    first = {}
    second = {}

    ds_root, metadata_key = _resolve_context(prefix="acic22")
    header, metadata = _load_metadata(
        metadata_key,
        expected_prefix=ds_root,
        use_cache=False,
        require_dataset_fields=True,
    )
    for idx in indices:
        first[idx] = _resolve_dataset_key(header, metadata[idx])

    clear_metadata_cache()

    ds_root_2, metadata_key_2 = _resolve_context(prefix="acic22")
    header_2, metadata_2 = _load_metadata(
        metadata_key_2,
        expected_prefix=ds_root_2,
        use_cache=False,
        require_dataset_fields=True,
    )
    for idx in indices:
        second[idx] = _resolve_dataset_key(header_2, metadata_2[idx])

    assert first == second


