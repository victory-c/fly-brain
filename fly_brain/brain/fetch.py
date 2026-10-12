"""Download the prebuilt brain instead of building it: brain.npz, brain_meta.parquet and web_data/atlas.npz.

    python -m brain.fetch              # about 220 MB into fly_brain/, each file checked against SHA256SUMS
    python -m brain.fetch --force      # download again even if the files are there and pass the check

The files are what `python -m brain.connectome` and `python -m brain.atlas` write from the male CNS v1.0 tables;
that build needs the 1.1 GB download and about 20 GB of RAM, more than a laptop or Colab has. They are published
as assets of a GitHub release of this repository, with their SHA256SUMS, by tools/publish_brain.sh. A file is
written to a .part file first and moved into place only after its checksum matches.

The files are derived from the male CNS v1.0 connectome (HHMI Janelia FlyEM, Cambridge Connectomics Group and
Google Research; CC-BY 4.0) and carry its licence: cite Berg et al., Cell 189, 5504 (2026),
doi:10.1016/j.cell.2026.08.015.
"""
import argparse
import hashlib
import urllib.error
import urllib.request

from .connectome import ATLAS, META, NPZ

REPO = "victory-c/fly-brain"
RELEASE = "brain-v1"
FILES = {"brain.npz": NPZ, "brain_meta.parquet": META, "atlas.npz": ATLAS}  # release asset -> where it goes
CHUNK = 1 << 20


def release_url(tag=RELEASE):
    return f"https://github.com/{REPO}/releases/download/{tag}/"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(CHUNK):
            h.update(chunk)
    return h.hexdigest()


def _open(url):
    try:
        return urllib.request.urlopen(url, timeout=60)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{url}: HTTP {e.code}. Is the release published? (tools/publish_brain.sh; "
                         "or build the files yourself with `python -m brain.connectome` and `python -m brain.atlas`)")
    except urllib.error.URLError as e:
        raise SystemExit(f"{url}: {e.reason}")


def checksums(base):
    """{asset name: sha256 hex} from the release's SHA256SUMS (sha256sum format)."""
    with _open(base + "SHA256SUMS") as r:
        lines = r.read().decode().splitlines()
    return {name.lstrip("*"): digest for digest, name in (line.split(maxsplit=1) for line in lines if line.strip())}


def download(url, dest, digest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    h, done, shown = hashlib.sha256(), 0, -1
    with _open(url) as r, open(part, "wb") as out:
        total = int(r.headers.get("Content-Length") or 0)
        while chunk := r.read(CHUNK):
            out.write(chunk)
            h.update(chunk)
            done += len(chunk)
            if total and (tenth := 10 * done // total) != shown:
                shown = tenth
                print(f"  {dest.name}: {done / 1e6:6.0f} of {total / 1e6:.0f} MB", flush=True)
    if h.hexdigest() != digest:
        part.unlink()
        raise SystemExit(f"{dest.name}: checksum mismatch (got {h.hexdigest()[:12]}, expected {digest[:12]}); "
                         "nothing was replaced, try again")
    part.replace(dest)


def fetch(tag=RELEASE, base=None, force=False):
    """Put the release's files in place, skipping those already there with the right checksum."""
    base = base or release_url(tag)
    sums = checksums(base)
    for name, dest in FILES.items():
        if name not in sums:
            raise SystemExit(f"{base}SHA256SUMS lists no {name}")
        if not force and dest.exists() and sha256(dest) == sums[name]:
            print(f"{dest.name}: already there")
            continue
        download(base + name, dest, sums[name])
        print(f"{dest.name}: ok -> {dest}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--tag", default=RELEASE, help=f"release tag (default {RELEASE})")
    ap.add_argument("--force", action="store_true", help="download even if the files are there")
    a = ap.parse_args()
    fetch(a.tag, force=a.force)


if __name__ == "__main__":
    main()
