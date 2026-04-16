from pathlib import Path
import pandas as pd
import cidl

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data_processing" / "raw_data_for_validation"
GROUND_TRUTH_PATH = RAW_DIR / "ground_truth.csv"


def test_r3_1_seeded_selection_is_reproducible(require_live_s3):
    first = cidl.select_indices(n=10, seed=123)
    second = cidl.select_indices(n=10, seed=123)

    assert first == second
    assert first == sorted(first)
    assert len(first) == 10
    assert len(set(first)) == 10


def expected_indices_from_raw_truth(
    *,
    confounding_strength=None,
    confounding_source=None,
    impact_heterogeneity=None,
    idiosyncrasy_impacts=None,
) -> list[int]:
    truth = pd.read_csv(GROUND_TRUTH_PATH, dtype={"dataset.num": str})

    df = truth.copy()

    if confounding_strength is not None:
        df = df[df["Confounding Strength"] == confounding_strength]
    if confounding_source is not None:
        df = df[df["Confounding Source"] == confounding_source]
    if impact_heterogeneity is not None:
        df = df[df["Impact Heterogeneity"] == impact_heterogeneity]
    if idiosyncrasy_impacts is not None:
        df = df[df["Idiosyncrasy of Impacts"] == idiosyncrasy_impacts]

    return sorted(df["dataset.num"].astype(int).unique().tolist())


def test_r3_2_dgp_constrained_selection_matches_raw_truth_1(require_live_s3):
    selected = cidl.select_indices_dgp(
        n=None,
        confounding_strength="strong",
        confounding_source="A",
        prefix="acic22",
    )

    expected = expected_indices_from_raw_truth(
        confounding_strength="Strong",
        confounding_source="Scenario A",
    )

    assert expected
    assert selected
    assert selected == expected
    assert selected == sorted(selected)
    assert len(selected) == len(set(selected))


def test_r3_2_dgp_constrained_selection_matches_raw_truth_2(require_live_s3):
    selected = cidl.select_indices_dgp(
        n=None,
        confounding_strength="weak",
        confounding_source="B",
        impact_heterogeneity="large",
        idiosyncrasy_impacts="small",
        prefix="acic22",
    )

    expected = expected_indices_from_raw_truth(
        confounding_strength="Weak",
        confounding_source="Scenario B",
        impact_heterogeneity="Large",
        idiosyncrasy_impacts="Small",
    )

    assert expected
    assert selected
    assert len(expected) == 200
    assert len(selected) == 200
    assert selected == expected
    assert selected == sorted(selected)
    assert len(selected) == len(set(selected))


def test_r3_2_dgp_constrained_selection_matches_raw_truth_3(require_live_s3):
    selected = cidl.select_indices_dgp(
        n=None,
        confounding_strength="weak",
        confounding_source="B",
        impact_heterogeneity="small",
        idiosyncrasy_impacts="small",
        prefix="acic22",
    )

    expected = expected_indices_from_raw_truth(
        confounding_strength="Weak",
        confounding_source="Scenario B",
        impact_heterogeneity="Small",
        idiosyncrasy_impacts="Small",
    )

    assert expected
    assert selected
    assert len(expected) == 200
    assert len(selected) == 200
    assert selected == expected
    assert selected == sorted(selected)
    assert len(selected) == len(set(selected))