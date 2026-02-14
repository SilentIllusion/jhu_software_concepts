"""Sphinx configuration for the Grad Cafe analytics project."""

import os
import sys
from datetime import datetime

# Ensure the application source is importable for autodoc
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APP_SRC = os.path.join(PROJECT_ROOT, "src")
if APP_SRC not in sys.path:
    sys.path.insert(0, APP_SRC)

project = "Grad Cafe Analytics"
author = "Grad Cafe Team"
copyright = f"{datetime.now().year}, {author}"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "alabaster"
html_static_path = ["_static"]
