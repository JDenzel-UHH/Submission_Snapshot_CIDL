import cidl

def test_r7_1_same_loading_interface_across_contexts(monkeypatch, require_live_s3):
    acic22_1 = cidl.load_datasets(20)

    monkeypatch.setenv("CIDL_PREFIX", "acic22_practice")
    cidl.reset_config()
    practice_1 = cidl.load_datasets(20)

    acic22_2 = cidl.load_datasets(20, prefix="acic22")
    practice_2 = cidl.load_datasets(20, prefix="acic22_practice")

    assert acic22_1[20].equals(acic22_2[20])
    assert practice_1[20].equals(practice_2[20])
    assert not acic22_1[20].equals(practice_1[20])


def test_r7_2_active_context_is_exposed(monkeypatch):
    monkeypatch.setenv("CIDL_PREFIX", "acic22")
    cidl.reset_config()
    cfg = cidl.get_config()

    assert cfg.prefix == "acic22"
    assert cfg.metadata_key == "acic22/metadata/acic22_metadata.json"

    monkeypatch.setenv("CIDL_PREFIX", "acic22_practice")
    cidl.reset_config()
    cfg = cidl.get_config()

    assert cfg.prefix == "acic22_practice"
    assert cfg.metadata_key == "acic22_practice/metadata/acic22_practice_metadata.json"


