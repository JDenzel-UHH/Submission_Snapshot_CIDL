from pathlib import Path
import tarfile
import zipfile
import re

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"

SUSPICIOUS_REGEXES = [
    re.compile(
        r"(?im)\baws_access_key_id\b\s*[:=]\s*['\"]?[A-Za-z0-9][A-Za-z0-9._/+\\=-]{15,127}['\"]?"
    ),
    re.compile(
        r"(?im)\baws_secret_access_key\b\s*[:=]\s*['\"]?[A-Za-z0-9/+=][A-Za-z0-9._/+\\=-]{19,127}['\"]?"
    ),
    re.compile(
        r"(?m)\bAWS_ACCESS_KEY_ID\b\s*=\s*['\"]?[A-Za-z0-9][A-Za-z0-9._/+\\=-]{15,127}['\"]?"
    ),
    re.compile(
        r"(?m)\bAWS_SECRET_ACCESS_KEY\b\s*=\s*['\"]?[A-Za-z0-9/+=][A-Za-z0-9._/+\\=-]{19,127}['\"]?"
    ),
]

EXCLUDED_PATH_PARTS = {
    "tests\\outputs",
    "tests/outputs",
    ".venv_cidl\\",
    ".venv_cidl/",
}

TEXT_SUFFIXES = {".py", ".md", ".txt", ".toml", ".yml", ".yaml", ".json"}


def _assert_no_secrets(text: str, source: str) -> None:
    for rx in SUSPICIOUS_REGEXES:
        match = rx.search(text)
        assert match is None, f"Suspicious credential-like content found in {source}: {match.group(0)!r}"


def test_r6_1_no_credentials_embedded_in_submitted_artifacts():
    checked_files = []

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue

        path_str = str(path)

        if path.name == "test_r6_credentials.py":
            continue

        if any(part in path_str for part in EXCLUDED_PATH_PARTS):
            continue

        if path.suffix.lower() in TEXT_SUFFIXES:
            text = path.read_text(encoding="utf-8", errors="ignore")
            checked_files.append(path)
            _assert_no_secrets(text, str(path))

    assert checked_files, "No text-based submission artifacts were checked."


def test_r6_1_no_aws_credentials_files_in_submission():
    forbidden_paths = []

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue

        if path.name in {"credentials", "config"} and ".aws" in str(path.parent):
            forbidden_paths.append(path)

        if path.name in {".env", ".env.local"}:
            forbidden_paths.append(path)

    assert not forbidden_paths, f"AWS credential/config files found in submission: {forbidden_paths}"


def test_r6_1_no_credentials_embedded_in_dist_artifacts():
    assert DIST.exists(), "dist/ directory not found."

    archives = list(DIST.glob("*.whl")) + list(DIST.glob("*.tar.gz"))
    assert archives, "No distribution artifacts found in dist/."

    checked_entries = []

    for archive in archives:
        if archive.suffix == ".whl":
            with zipfile.ZipFile(archive, "r") as zf:
                for name in zf.namelist():
                    if name.endswith("tests/test_r6_credentials.py") or name.endswith("tests\\test_r6_credentials.py"):
                        continue
                    if Path(name).suffix.lower() in TEXT_SUFFIXES:
                        text = zf.read(name).decode("utf-8", errors="ignore")
                        checked_entries.append(f"{archive.name}:{name}")
                        _assert_no_secrets(text, f"{archive.name}:{name}")

        elif archive.name.endswith(".tar.gz"):
            with tarfile.open(archive, "r:gz") as tf:
                for member in tf.getmembers():
                    if member.name.endswith("tests/test_r6_credentials.py") or member.name.endswith("tests\\test_r6_credentials.py"):
                        continue
                    if member.isfile() and Path(member.name).suffix.lower() in TEXT_SUFFIXES:
                        extracted = tf.extractfile(member)
                        if extracted is None:
                            continue
                        text = extracted.read().decode("utf-8", errors="ignore")
                        checked_entries.append(f"{archive.name}:{member.name}")
                        _assert_no_secrets(text, f"{archive.name}:{member.name}")

    assert checked_entries, "No text-based files were checked inside dist artifacts."