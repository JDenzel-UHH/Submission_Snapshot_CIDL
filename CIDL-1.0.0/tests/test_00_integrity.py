from pathlib import Path
import pandas as pd
import pytest
import cidl

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data_processing" / "raw_data_for_validation"
INDICES = [1, 153, 547, 1195, 1233, 1480, 2069, 2395, 3093, 3400]
GROUND_TRUTH_PATH = RAW_DIR / "ground_truth.csv"

def raw_paths(idx: int) -> dict[str, Path]:
    s = f"{idx:04d}"
    return {
        "patient": RAW_DIR / f"acic_patient_{s}.csv",
        "patient_year": RAW_DIR / f"acic_patient_year_{s}.csv",
        "practice": RAW_DIR / f"acic_practice_{s}.csv",
        "practice_year": RAW_DIR / f"acic_practice_year_{s}.csv",
    }

def build_expected_from_raw(idx: int) -> pd.DataFrame:
    paths = raw_paths(idx)

    patient = pd.read_csv(paths["patient"])
    patient_year = pd.read_csv(paths["patient_year"])
    practice = pd.read_csv(paths["practice"])
    practice_year = pd.read_csv(paths["practice_year"])

    practice_year = practice_year.drop(columns=["Y"], errors="ignore")
    out = patient_year.merge(patient, on="id.patient", how="left")
    out = out.merge(practice, on="id.practice", how="left")
    out = out.merge(practice_year, on=["id.practice", "year"], how="left")
    return out

@pytest.mark.parametrize("idx", INDICES)
def test_data_matches_raw_data(require_live_s3, idx):
    observed = cidl.load_datasets(idx)[idx]
    expected = build_expected_from_raw(idx)

    observed = observed.sort_values(["id.patient", "year"]).reset_index(drop=True)
    expected = expected.sort_values(["id.patient", "year"]).reset_index(drop=True)

    observed = observed.reindex(sorted(observed.columns), axis=1)
    expected = expected.reindex(sorted(expected.columns), axis=1)

    pd.testing.assert_frame_equal(
        observed,
        expected,
        check_dtype=False,
    )



def build_expected_truth_from_raw(idx: int) -> pd.DataFrame:
    truth = pd.read_csv(GROUND_TRUTH_PATH, dtype={"dataset.num": str})
    out = truth[truth["dataset.num"] == f"{idx:04d}"].copy()
    out["dataset.num"] = out["dataset.num"].astype(int)
    return out

def test_truth_matches_raw_ground_truth(require_live_s3):
    for idx in INDICES:
        observed = cidl.load_truth([idx])[idx]
        expected = build_expected_truth_from_raw(idx)

        observed = observed.astype(object).where(pd.notna(observed), None)
        expected = expected.astype(object).where(pd.notna(expected), None)

        pd.testing.assert_frame_equal(
            observed.reset_index(drop=True),
            expected.reset_index(drop=True),
            check_dtype=False,
        )