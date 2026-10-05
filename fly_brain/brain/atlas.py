"""Where the neurons sit and which part of the nervous system each counts towards, for the brain maps on the pages.

The map shows each neuron at its cell body: the annotated soma position, or for neurons whose soma lies outside
the imaged volume the point where the neurite leaves it (tosomaLocation). Neurons with neither are not drawn.
Positions are shifted so the bounding box is centred on 0 and scaled by one factor so its longest side spans 2.
Built once into web_data/atlas.npz:

    python -m brain.atlas

Regions are for display only. A neuron is placed by the first of three lookups that knows it:
  1. a sensory neuron by its modality (the annotation `class` of sensory neurons),
  2. a central-brain neuron by its circuit (mushroom body, central complex, antennal lobe, SEZ projection neurons),
  3. anything else by the dataset's `superclass` (optic lobe, descending, ascending/nerve cord, motor/efferent);
central-brain neurons left over count as the subesophageal zone when their cell type is named after one of its
neuropils (gnathal ganglia, prow), else as "other".
"""
import numpy as np
import pandas as pd

from .connectome import ANNOTATIONS, META, ROOT

ATLAS = ROOT / "web_data" / "atlas.npz"
CLOUD_HZ = 40.0  # firing rate drawn at full brightness on the maps

REGIONS = [  # (id, label) in display order: sensory, central brain, output
    ("visual", "Optic lobes & visual neurons"), ("olfactory", "Olfactory system"), ("gustatory", "Gustatory neurons"),
    ("somatosensory", "Somatosensory neurons"), ("sez", "Subesophageal zone (SEZ)"), ("mushroom_body", "Mushroom body"),
    ("central_complex", "Central complex"), ("other", "Other central brain"), ("descending", "Descending neurons"),
    ("vnc", "Ventral nerve cord"), ("motor", "Motor & efferent neurons"),
]

BY_MODALITY = {
    "gustatory": "gustatory", "chemosensory": "gustatory",
    "olfactory": "olfactory",
    "visual": "visual",
    "mechanosensory": "somatosensory", "mechanosensory_tbc": "somatosensory", "mechanosensory_tactile": "somatosensory",
    "mechanosensory_proprioceptive": "somatosensory", "hygrosensory": "somatosensory", "thermosensory": "somatosensory",
}
BY_CIRCUIT = {
    "Kenyon_Cell": "mushroom_body", "MBON": "mushroom_body", "DAN": "mushroom_body",
    "CX": "central_complex",
    "ALPN": "olfactory", "ALLN": "olfactory", "ALIN": "olfactory", "ALON": "olfactory",
    "SEZPN": "sez",
}
BY_SUPERCLASS = {
    "ol_intrinsic": "visual", "ol_sensory": "visual", "visual_projection": "visual",
    "visual_projection_tbc": "visual", "visual_centrifugal": "visual",
    "descending_neuron": "descending", "descending_neuron_tbc": "descending", "sensory_descending": "descending",
    "vnc_intrinsic": "vnc", "vnc_tbc": "vnc", "ascending_neuron": "vnc",
    "vnc_sensory": "somatosensory", "vnc_sensory_tbc": "somatosensory", "cb_sensory": "somatosensory", "cb_sensory_tbc": "somatosensory",
    "sensory_ascending": "somatosensory", "sensory_ascending_tbc": "somatosensory",
    "cb_motor": "motor", "vnc_motor": "motor", "cb_efferent": "motor", "vnc_efferent": "motor",
    "efferent_ascending": "motor", "efferent_descending": "motor",
}
SEZ_NEUROPILS = ("GNG", "PRW")  # gnathal ganglia, prow


def regions(meta):
    """Region id of every row of `meta` (brain_meta.parquet), as a numpy array of str."""
    cls, sup, typ = (meta[c].fillna("").astype(str) for c in ("class", "superclass", "type"))
    sez = (sup == "cb_intrinsic") & typ.str.startswith(SEZ_NEUROPILS)
    out = pd.Series("other", index=meta.index)
    out[sez] = "sez"
    for column, table in ((sup, BY_SUPERCLASS), (cls, BY_CIRCUIT), (cls, BY_MODALITY)):  # later lookups win
        hit = column.map(table)
        out[hit.notna()] = hit[hit.notna()]
    return out.to_numpy(dtype=str)


def point_cloud():
    """(xyz (P, 3) float32 in [-1, 1], row (P,) int64 simulator index of each point)."""
    if not ATLAS.exists():
        build()
    with np.load(ATLAS) as a:
        return a["xyz"], a["row"]


def _xyz_columns(locations):
    """A column of [x, y, z] lists (or missing values) as an (n, 3) float array, NaN where missing or malformed."""
    out = np.full((len(locations), 3), np.nan)
    good = locations.map(lambda v: getattr(v, "__len__", None) is not None and len(v) == 3).to_numpy(bool)
    if good.any():
        out[good] = np.vstack(locations[good].to_numpy())
    return out


def build():
    meta = pd.read_parquet(META, columns=["row", "bodyId"])
    where = (pd.read_feather(ANNOTATIONS, columns=["bodyId", "somaLocation", "tosomaLocation"])
             .drop_duplicates("bodyId").set_index("bodyId").reindex(meta["bodyId"]))
    soma, exit_point = _xyz_columns(where["somaLocation"]), _xyz_columns(where["tosomaLocation"])
    xyz = np.where(np.isnan(soma).any(axis=1, keepdims=True), exit_point, soma)
    drawn = ~np.isnan(xyz).any(axis=1)
    xyz = xyz[drawn]
    centre = (xyz.max(axis=0) + xyz.min(axis=0)) / 2
    scale = 2 / np.ptp(xyz, axis=0).max()
    ATLAS.parent.mkdir(exist_ok=True)
    np.savez(ATLAS, xyz=((xyz - centre) * scale).astype(np.float32), row=meta["row"].to_numpy(np.int64)[drawn])
    print(f"{drawn.sum():,} of {len(meta):,} neurons drawn -> {ATLAS}")


if __name__ == "__main__":
    build()
