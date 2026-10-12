"""brain/fetch.py against a local stand-in for the GitHub release (file:// URLs); no network.

    python -m pytest tests/test_fetch.py
"""
import hashlib

import pytest

from brain import fetch


@pytest.fixture
def release(tmp_path, monkeypatch):
    """A release directory with three small assets and their SHA256SUMS; FILES redirected into tmp_path/out."""
    assets = tmp_path / "release"
    assets.mkdir()
    lines = []
    for i, name in enumerate(fetch.FILES):
        data = bytes([i]) * (3 * fetch.CHUNK + 17)  # several chunks, so the progress lines run
        (assets / name).write_bytes(data)
        lines.append(f"{hashlib.sha256(data).hexdigest()}  {name}")
    (assets / "SHA256SUMS").write_text("\n".join(lines) + "\n")
    out = tmp_path / "out"
    monkeypatch.setattr(fetch, "FILES", {"brain.npz": out / "brain.npz", "brain_meta.parquet": out / "brain_meta.parquet",
                                         "atlas.npz": out / "web_data" / "atlas.npz"})
    return assets.as_uri() + "/", assets, out


def test_downloads_checks_and_skips(release, capsys):
    base, assets, out = release
    fetch.fetch(base=base)
    for name, dest in fetch.FILES.items():
        assert dest.read_bytes() == (assets / name).read_bytes()
    assert not list(out.rglob("*.part"))
    fetch.fetch(base=base)
    assert capsys.readouterr().out.count("already there") == 3


def test_a_bad_download_replaces_nothing(release):
    base, assets, out = release
    fetch.fetch(base=base)
    good = fetch.FILES["brain.npz"].read_bytes()
    (assets / "brain.npz").write_bytes(b"corrupted")
    with pytest.raises(SystemExit, match="checksum mismatch"):
        fetch.fetch(base=base, force=True)
    assert fetch.FILES["brain.npz"].read_bytes() == good
    assert not list(out.rglob("*.part"))


def test_missing_release_explains_itself(tmp_path):
    with pytest.raises(SystemExit, match="nowhere"):
        fetch.fetch(base=(tmp_path / "nowhere").as_uri() + "/")
