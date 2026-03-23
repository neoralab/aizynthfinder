import os
import sys

sys.path.insert(0, os.path.abspath("."))

project = "aizynthfinder"
copyright = "2020-2025, Molecular AI group"
author = "Molecular AI group"
release = "4.4.1"

extensions = [
    "sphinx.ext.autodoc",
]
autodoc_member_order = "bysource"
autodoc_typehints = "description"

html_theme = "alabaster"
html_theme_options = {
    "description": "A fast, robust and flexible software for retrosynthetic planning",
    "fixed_sidebar": True,
}
