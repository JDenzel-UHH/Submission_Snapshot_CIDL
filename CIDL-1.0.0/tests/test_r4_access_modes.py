import pandas as pd
from pathlib import Path
import cidl
from cidl.objectkey_resolution import _load_metadata, _resolve_context


# Redundant with R1.2, kept here as direct evidence for R4.1
def test_r4_1_in_memory_loading(require_live_s3, representative_indices):
    out = cidl.load_datasets(representative_indices)

    assert isinstance(out, dict)
    assert set(out.keys()) == set(representative_indices)
    assert all(isinstance(out[idx], pd.DataFrame) for idx in representative_indices)



def test_r4_2_sequential_iteration(require_live_s3, representative_indices):
    iterator = cidl.iter_datasets(representative_indices)

    assert iterator is not None
    assert not isinstance(iterator, dict)

    items = list(iterator)

    assert len(items) == len(representative_indices)
    assert [idx for idx, _ in items] == representative_indices
    assert all(isinstance(idx, int) for idx, _ in items)
    assert all(isinstance(df, pd.DataFrame) for _, df in items)


def test_r4_3_local_download(require_live_s3, representative_indices, tmp_path):
    out_dir = tmp_path / "downloads"
    out_dir.mkdir(parents=True, exist_ok=True)

    ds_root, metadata_key = _resolve_context(prefix="acic22")
    _, metadata = _load_metadata(
        metadata_key,
        expected_prefix=ds_root,
        use_cache=False,
        require_dataset_fields=True,
    )

    expected_names = {
        Path(str(metadata[idx]["filename"])).name
        for idx in representative_indices
    }

    written = cidl.download_datasets(
        representative_indices,
        out_dir,
        overwrite=True,
    )

    written_names = {path.name for path in written}
    files_in_dir = {p.name for p in out_dir.iterdir() if p.is_file()}

    assert len(written) == len(representative_indices)
    assert all(path.exists() for path in written)
    assert all(path.parent == out_dir for path in written)
    assert written_names == expected_names
    assert files_in_dir == expected_names
