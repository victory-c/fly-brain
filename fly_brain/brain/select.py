"""Pick neurons by name, class, side, transmitter or position instead of by simulator row.

    brain = Brain()
    mn9 = brain.select(instance=["MN9_L", "MN9_R"])
    dns = brain.select(superclass="descending_neuron", side="L")
    dnp = brain.select(type="DNp*")                      # * and ? are wildcards
    near = brain.select(near=("MN9_L", 20.0))            # somata within 20 um of MN9_L's soma
    brain.meta.loc[dns, ["bodyId", "type", "side"]]      # look the selected rows up

Every filter takes one value or a list (a neuron passes if it matches any of them); filters combine with AND.
A value that matches no neuron at all raises KeyError and names the closest values, so a typo cannot silently
select nothing. The result is a sorted int64 array of simulator rows, the indices Engine, experiment() and
BrainLoop take.

Filters and the brain_meta.parquet column each one reads:
  type, instance, superclass, transmitter    the column of that name (male CNS v1.0 annotations; transmitter as
                                             chosen in brain/connectome.py)
  class_                                     `class` (a Python keyword, hence the underscore)
  side                                       "L" or "R": somaSide, else the side the root enters (sensory neurons)
  region                                     the display region of brain/atlas.py (atlas.REGIONS), e.g. "descending"
  near=(centre, radius_um)                   soma within radius_um micrometres of centre: an (x, y, z) in um, a
                                             simulator row, or an instance name

Positions are the soma locations of the male-CNS annotations, in micrometres (8 nm voxels); for a neuron whose
soma lies outside the imaged volume, the point where its neurite leaves it (sensory neurons such as the taste
GRNs). They come from web_data/atlas.npz (python -m brain.atlas, or python -m brain.fetch). Neurons with neither
have no position, and near= never selects them.
"""
import difflib
import re

import numpy as np
import pandas as pd

COLUMNS = {"type": "type", "instance": "instance", "superclass": "superclass", "class_": "class",
           "transmitter": "transmitter", "side": "side", "region": "region"}


def select(brain, *, near=None, **filters):
    meta = brain.meta
    keep = np.ones(brain.n, dtype=bool)
    for name, wanted in filters.items():
        if wanted is None:
            continue
        if name not in COLUMNS:
            raise TypeError(f"select() has no filter {name!r}; it takes {', '.join(COLUMNS)} and near")
        keep &= _matches(_values(meta, name), wanted, name)
    if near is not None:
        keep &= _near(brain, near)
    return np.flatnonzero(keep).astype(np.int64)


def load_positions(path, n):
    """(n, 3) float64 micrometres from atlas.npz, NaN for the neurons it has no position for."""
    try:
        stored = np.load(path)
    except FileNotFoundError:
        raise SystemExit(f"{path} not found: download it with `python -m brain.fetch`, "
                         "or build it with `python -m brain.atlas`") from None
    with stored:
        if "xyz_um" not in stored.files:
            raise SystemExit(f"{path} predates micrometre positions; rebuild it with `python -m brain.atlas`")
        out = np.full((n, 3), np.nan)
        out[stored["row"]] = stored["xyz_um"]
    return out


def _values(meta, name):
    if name == "region":
        from .atlas import regions
        if "region" not in meta:
            meta["region"] = regions(meta)
    return meta[COLUMNS[name]].fillna("").astype(str).to_numpy()


def _matches(values, wanted, name):
    if isinstance(wanted, str):
        wanted = [wanted]
    elif isinstance(wanted, (list, tuple, set, np.ndarray, pd.Series)):
        wanted = list(wanted)
    else:
        raise TypeError(f"{name}= takes names (str) or a list of them, got {wanted!r}")
    hit = np.zeros(len(values), dtype=bool)
    for value in wanted:
        if not isinstance(value, str):
            raise TypeError(f"{name}= takes names (str), got {value!r}")
        if "*" in value or "?" in value:
            pattern = re.escape(value).replace(r"\*", ".*").replace(r"\?", ".")
            one = pd.Series(values).str.fullmatch(pattern).to_numpy()
        else:
            one = values == value
        if not one.any():
            close = difflib.get_close_matches(value, sorted(set(values) - {""}), n=5, cutoff=0.5)
            hint = f"; closest: {', '.join(close)}" if close else ""
            raise KeyError(f"no neuron has {name}={value!r}{hint}")
        hit |= one
    return hit


def _near(brain, near):
    try:
        centre, radius = near
    except (TypeError, ValueError):
        raise TypeError("near= takes (centre, radius_um)") from None
    xyz = brain.positions
    if isinstance(centre, str):
        row = select(brain, instance=centre)
        if len(row) != 1:
            raise KeyError(f"near=: instance {centre!r} names {len(row)} neurons, not one")
        centre = xyz[row[0]]
    elif isinstance(centre, (int, np.integer)):
        centre = xyz[centre]
    centre = np.asarray(centre, dtype=float)
    if centre.shape != (3,):
        raise TypeError(f"near=: centre must be (x, y, z) in um, a row or an instance name, got {near[0]!r}")
    if np.isnan(centre).any():
        raise ValueError(f"near=: neuron {near[0]!r} has no position")
    return np.linalg.norm(xyz - centre, axis=1) <= float(radius)  # NaN (no position) compares False
