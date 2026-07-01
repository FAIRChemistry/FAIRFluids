"""Execute the tutorial notebooks in place (validate + populate outputs).

Run with::

    uv run python transition_water/tutorials/_run_notebooks.py
"""

from __future__ import annotations

import os
import sys

import nbformat
from nbclient import NotebookClient

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir))

NOTEBOOKS = [
    os.path.join(ROOT, "transition_water", "Walkthrough_Symbolic_Models.ipynb"),
    os.path.join(HERE, "01_declare_models.ipynb"),
    os.path.join(HERE, "02_frequentist_fitting.ipynb"),
    os.path.join(HERE, "03_bayesian_inference.ipynb"),
    os.path.join(HERE, "04_fluid_selectors.ipynb"),
]


def run(path: str) -> None:
    nb = nbformat.read(path, as_version=4)
    client = NotebookClient(
        nb,
        timeout=1200,
        kernel_name="python3",
        resources={"metadata": {"path": HERE}},
    )
    client.execute()
    nbformat.write(nb, path)
    print("OK  ", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    targets = sys.argv[1:] or NOTEBOOKS
    for nb_path in targets:
        run(nb_path)
    print("all notebooks executed")
