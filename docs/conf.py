"""Sphinx configuration for the documentation published on Read the Docs."""

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

project = "ccd-superres"
author = "ccd-superres contributors"
copyright = "2026, ccd-superres contributors"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinxcontrib.mermaid",
]

myst_enable_extensions = ["dollarmath", "amsmath", "colon_fence"]
myst_fence_as_directive = ["mermaid"]
myst_heading_anchors = 3

exclude_patterns = ["_build", "diagrams/*.py"]
html_theme = "furo"
html_title = "Scanning lensless sensor super-resolution"
autodoc_member_order = "bysource"


def copy_explorer(app, exception):
    """Publish the trade-off explorer page alongside the documentation."""
    if exception is None and app.builder.format == "html":
        shutil.copytree(ROOT / "explorer", Path(app.outdir) / "explorer", dirs_exist_ok=True)


def setup(app):
    app.connect("build-finished", copy_explorer)
