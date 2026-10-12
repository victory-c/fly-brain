#!/usr/bin/env bash
# Publish the built brain as a GitHub release, so others can `python -m brain.fetch` instead of building it
# (the build needs the 1.1 GB male CNS download and about 20 GB of RAM). Run it where fly_brain/brain.npz and
# fly_brain/data/ are (the OCF node), from anywhere in the repo:
#   bash tools/publish_brain.sh [tag]        # default brain-v1, the tag brain/fetch.py downloads
# 1. rebuilds web_data/atlas.npz (python -m brain.atlas), so it carries the micrometre positions brain.select uses;
# 2. writes SHA256SUMS and the release notes to fly_brain/release/ (gitignored);
# 3. uploads brain.npz, brain_meta.parquet, atlas.npz and SHA256SUMS with `gh release create` if gh is installed
#    and logged in here; otherwise prints the commands to finish from a machine that has gh.
set -euo pipefail
cd "$(dirname "$0")/../fly_brain"
TAG=${1:-brain-v1}
PY=${PY:-../venv/bin/python}
FILES=(brain.npz brain_meta.parquet web_data/atlas.npz)

for f in brain.npz brain_meta.parquet; do
  [ -s "$f" ] || { echo "fly_brain/$f missing: build it first with python -m brain.connectome" >&2; exit 1; }
done
"$PY" -m brain.atlas
mkdir -p release
"$PY" - "${FILES[@]}" > release/SHA256SUMS <<'PYEOF'
import hashlib, sys
from pathlib import Path
for f in sys.argv[1:]:
    h = hashlib.sha256()
    with open(f, "rb") as fh:
        while chunk := fh.read(1 << 20):
            h.update(chunk)
    print(f"{h.hexdigest()}  {Path(f).name}")
PYEOF
"$PY" - "$TAG" "$(git rev-parse --short HEAD)" "${FILES[@]}" > release/NOTES.md <<'PYEOF'
import sys
from pathlib import Path
import numpy as np
tag, commit, files = sys.argv[1], sys.argv[2], sys.argv[3:]
with np.load("brain.npz") as b:
    n, edges = len(b["ptr"]) - 1, len(b["post"])
print(f"""The prebuilt whole male CNS for the simulator: {n:,} neurons, {edges:,} connected pairs.
Download with `python -m brain.fetch` (from `fly_brain/`); it checks every file against `SHA256SUMS`.

| File | Size | What |
|---|---|---|""")
what = {"brain.npz": "signed synapse counts, CSR by presynaptic neuron (`python -m brain.connectome`)",
        "brain_meta.parquet": "one row per neuron: bodyId, type, instance, superclass, side, transmitter, ...",
        "atlas.npz": "soma positions: page coordinates and micrometres (`python -m brain.atlas`)"}
for f in files:
    p = Path(f)
    print(f"| `{p.name}` | {p.stat().st_size / 1e6:.0f} MB | {what[p.name]} |")
print(f"""
Built by this repository at commit {commit}.

**Data licence.** These files are derived from the male CNS v1.0 connectome (HHMI Janelia FlyEM, Cambridge
Connectomics Group and Google Research), which is licensed CC-BY 4.0 (https://male-cns.janelia.org). If you use
them, cite: Berg S, Beckett IR, Costa M, Schlegel P, Januszewski M, et al. Sexual dimorphism in the complete
Drosophila male central nervous system connectome. *Cell* 189(18):5504-5526.e15 (2026).
doi:10.1016/j.cell.2026.08.015. The code that built them is MIT-licensed (see LICENSE).""")
PYEOF
cat release/SHA256SUMS

if command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then
  gh release create "$TAG" --repo victory-c/fly-brain --title "Prebuilt brain ($TAG)" --notes-file release/NOTES.md \
    "${FILES[@]}" release/SHA256SUMS
else
  here=$(pwd)
  cat <<MSG

gh is not available here. From a machine with gh (logged in as the repo owner), in an empty directory:
  scp 'hpc:$here/{brain.npz,brain_meta.parquet,web_data/atlas.npz,release/SHA256SUMS,release/NOTES.md}' .
  gh release create $TAG --repo victory-c/fly-brain --title "Prebuilt brain ($TAG)" --notes-file NOTES.md \\
    brain.npz brain_meta.parquet atlas.npz SHA256SUMS
MSG
fi
