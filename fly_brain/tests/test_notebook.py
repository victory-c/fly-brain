"""notebooks/00_quickstart.ipynb runs top to bottom on the synthetic brain (CPU, about half a minute).

    python -m pytest tests/test_notebook.py        # needs nbclient and ipykernel; skipped without them

The notebook and the brain package are copied next to a synthetic brain in a temporary directory, so this
checks the notebook's code paths and names, not the numbers of the real connectome.
"""
import shutil
from pathlib import Path

import pytest

from tests.synthetic_brain import write

nbclient = pytest.importorskip("nbclient")
nbformat = pytest.importorskip("nbformat")
pytest.importorskip("ipykernel")
pytest.importorskip("matplotlib")

REPO = Path(__file__).resolve().parents[2]
NOTEBOOK = REPO / "notebooks" / "00_quickstart.ipynb"


def test_quickstart_runs(tmp_path, monkeypatch):
    shutil.copytree(REPO / "fly_brain" / "brain", tmp_path / "fly_brain" / "brain",
                    ignore=shutil.ignore_patterns("__pycache__"))
    (tmp_path / "notebooks").mkdir()
    shutil.copy(NOTEBOOK, tmp_path / "notebooks")
    write(tmp_path / "fly_brain")
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "")  # the CPU branch, wherever the test runs
    nb = nbformat.read(tmp_path / "notebooks" / NOTEBOOK.name, as_version=4)
    nbclient.NotebookClient(nb, timeout=300, kernel_name="python3",
                            resources={"metadata": {"path": str(tmp_path / "notebooks")}}).execute()
    printed = "".join(o.get("text", "") for c in nb.cells if c.cell_type == "code" for o in c.get("outputs", []))
    assert "with all 2 SugarIN neurons silenced: [0. 0.] Hz" in printed  # the synthetic brain's one route to MN9
