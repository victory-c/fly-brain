#!/usr/bin/env python3
"""Score Track B runs (runs/predictions.py) by the preregistered rule: a signed row passes on a brain if its difference has
the expected sign and is at least half as large as the same row's difference on the real wiring. Null rows are reported, not scored.
A row that does not have the expected sign on the real wiring passes on no brain.

    python3 tools/track_b_score.py DIR     # DIR holds r0.json and one json per rewired brain
"""
import json
import re
import sys
from pathlib import Path


def main():
    d = Path(sys.argv[1])
    ref = {r["id"]: r for r in json.loads((d / "r0.json").read_text())["signed"]}
    out = {}
    for f in sorted(d.glob("*.json")):
        if f.name == "scores.json":
            continue
        rows = json.loads(f.read_text())["signed"]
        ok = {r["id"]: bool(r["as_expected"] and ref[r["id"]]["as_expected"] and abs(r["difference_hz"]) >= 0.5 * abs(ref[r["id"]]["difference_hz"])) for r in rows}
        out[f.stem] = {"score": sum(ok.values()) / len(ok), "rows": ok}
        print(f.stem, round(out[f.stem]["score"], 3), [k for k, v in ok.items() if not v])
    (d / "scores.json").write_text(json.dumps(out, indent=1))
    if "--by-rung" in sys.argv:  # section 6: a rung's score is the mean over its draws, for each scale; files are <rung>_s<draw>[_w<scale>].json
        groups = {}
        for stem, s in out.items():
            m = re.fullmatch(r"(r\d+)(?:_s\d+)?(?:_w([\d.]+))?", stem)
            groups.setdefault((m[1], m[2] or "0.47"), []).append(s["score"])
        print("| Rung | Scale | Draws | Mean score |\n|---|---|---|---|")
        for (rung, scale), scores in sorted(groups.items()):
            print(f"| {rung} | {scale} | {len(scores)} | {sum(scores) / len(scores):.3f} |")


if __name__ == "__main__":
    main()
