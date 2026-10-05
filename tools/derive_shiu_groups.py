"""Derive the stimulus groups of brain/stimuli.py from Shiu et al. 2024 -> fly_brain/brain/shiu_groups.json.

Shiu et al. drive named sets of FlyWire neurons (sugar, water, bitter and Ir94e GRNs of one labellum; three
Johnston's organ populations) in figures.ipynb of github.com/philshiu/Drosophila_brain_model (MIT). The male CNS
has different bodies but shares FlyWire's cell-type names, so each set is carried over by type:

  1. look up the FlyWire cell type of every neuron in each set (flyconnectome/flywire_annotations, CC-BY 4.0)
  2. give each cell type to the set holding most of its neurons (LB3c: 9 sugar vs 7 water -> sugar)
  3. in the male CNS, the group is every neuron of those types, on both sides

    python tools/derive_shiu_groups.py
"""
import io
import json
import re
import urllib.request
from collections import Counter
from pathlib import Path

import pandas as pd

NOTEBOOK = "https://raw.githubusercontent.com/philshiu/Drosophila_brain_model/main/figures.ipynb"
FLYWIRE = ("https://raw.githubusercontent.com/flyconnectome/flywire_annotations/main/"
           "supplemental_files/Supplemental_file1_neuron_annotations.tsv")
OUT = Path(__file__).resolve().parents[1] / "fly_brain" / "brain" / "shiu_groups.json"
SETS = {"sugar": "neu_sugar", "water": "neu_water", "bitter": "neu_bitter", "ir94e": "neu_ir94e",
        "jo_ce": "neu_JON_CE", "jo_f": "neu_JON_F", "jo_dm": "neu_JON_D_m"}


def fetch(url):
    with urllib.request.urlopen(url) as r:
        return r.read()


def main():
    cells = json.loads(fetch(NOTEBOOK))["cells"]
    code = "\n".join("".join(c["source"]) for c in cells if c["cell_type"] == "code")
    ids = {}
    for name, var in SETS.items():
        body = re.search(rf"\b{var}\s*=\s*\[([^\]]*)\]", code).group(1)
        ids[name] = [int(x) for x in re.findall(r"\d{15,}", body)]
    ann = pd.read_csv(io.BytesIO(fetch(FLYWIRE)), sep="\t", usecols=["root_id", "cell_type"], low_memory=False)
    type_of = ann.dropna().set_index("root_id")["cell_type"]

    counts = {name: Counter(type_of.get(i) for i in members if i in type_of.index) for name, members in ids.items()}
    owner = {}
    for name, c in counts.items():
        for t, k in c.items():
            if "unclear" not in t and k > owner.get(t, (None, 0))[1]:
                owner[t] = (name, k)
    groups = {name: {"types": sorted(t for t, (o, _) in owner.items() if o == name),
                     "shiu_neurons": len(ids[name]), "flywire_types": dict(counts[name].most_common())}
              for name in SETS}
    OUT.write_text(json.dumps({"source": [NOTEBOOK, FLYWIRE], "groups": groups}, indent=1) + "\n")
    for name, g in groups.items():
        print(f"{name:7s} {g['shiu_neurons']:3d} Shiu neurons -> {', '.join(g['types'])}")


if __name__ == "__main__":
    main()
