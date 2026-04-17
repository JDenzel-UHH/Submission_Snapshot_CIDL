
from tqdm import tqdm
import math
import pandas as pd
import cidl


def test_r4_2_sequential_iteration_smoke_large_batch(require_live_s3):
    selection = range(1346, 1446)

    returned_indices = []
    diffs = []

    iterator = cidl.iter_datasets(
        selection,
        columns=["year", "Z", "Y"],
    )

    for idx, df in tqdm(iterator, total=len(selection), desc="iter_datasets smoke test"):
        returned_indices.append(idx)

        post_period = df.loc[df["year"].isin([3, 4]), ["Z", "Y"]]

        mean_treated = post_period.loc[post_period["Z"] == 1, "Y"].mean()
        mean_untreated = post_period.loc[post_period["Z"] == 0, "Y"].mean()

        assert pd.notna(mean_treated), f"mean_treated is NaN for idx={idx}"
        assert pd.notna(mean_untreated), f"mean_untreated is NaN for idx={idx}"

        diffs.append(float(mean_treated - mean_untreated))

    assert returned_indices == list(selection)
    assert len(diffs) == len(selection)
    assert all(isinstance(d, float) for d in diffs)
    assert all(math.isfinite(d) for d in diffs)