"""Named neuron groups to drive and read out, after the experiments of Shiu et al. 2024.

The input groups are Shiu's sets of gustatory receptor neurons (GRNs) and Johnston's organ neurons (JONs),
carried over to the male CNS by cell type (tools/derive_shiu_groups.py -> shiu_groups.json):

  sugar   LB3b-d, LB4b      labellar sugar GRNs (Gr64f)      -> proboscis extension via MN9
  water   LB3a              labellar water GRNs (ppk28)      -> also feeding
  bitter  LB1a-d            labellar bitter GRNs (Gr66a)     -> suppresses sugar-evoked feeding
  ir94e   LB1e, LB2a-c      Ir94e GRNs                       -> mildly suppresses feeding
  jo_ce   JO-C/E types      antennal displacement (JO-CE)    -> antennal grooming
  jo_f    JO-F types        JO-F                             -> grooming
  jo_dm   JO-DA/DP/mz       JO-D and -m

Shiu drove one labellum (about 20 neurons per set); here a group spans both sides unless side= is given.
"""
import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from .connectome import META

GROUPS_FILE = Path(__file__).with_name("shiu_groups.json")
SHIU_HZ = 150.0  # Shiu's default Poisson rate (r_poi)


@lru_cache(maxsize=1)
def shiu_groups():
    return {name: g["types"] for name, g in json.loads(GROUPS_FILE.read_text())["groups"].items()}


@lru_cache(maxsize=1)
def neurons():
    """brain_meta with each neuron's side: somaSide, else the side its root enters (sensory neurons)."""
    meta = pd.read_parquet(META)
    meta["side"] = meta["somaSide"].where(meta["somaSide"].isin(["L", "R"]), meta["rootSide"])
    return meta


def group(name, side=None):
    """Simulator indices of one of shiu_groups(), optionally one side ("L" or "R")."""
    m = neurons()
    mask = m["type"].isin(shiu_groups()[name])
    if side:
        mask &= m["side"] == side
    return m.loc[mask, "row"].to_numpy(np.int64)


def instance(name):
    """Simulator index of a named neuron instance such as "MN9_L"."""
    m = neurons()
    hit = m.index[m["instance"] == name]
    if len(hit) != 1:
        raise KeyError(f"{name}: {len(hit)} matches")
    return int(m.loc[hit[0], "row"])


def mn9():
    """The two MN9 motor neurons (proboscis extension, Shiu's feeding readout): [left, right]."""
    return np.array([instance("MN9_L"), instance("MN9_R")], dtype=np.int64)
