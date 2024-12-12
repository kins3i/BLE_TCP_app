# Configuration file for the Sphinx documentation builder.
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import pathlib
import sys

PROJECT_ROOT_DIR = pathlib.Path(__file__).parent.parent.resolve()
cwd = os.getcwd()
project_root = os.path.dirname(cwd)
sys.path.insert(0, project_root)

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'BLE and TCP app'
copyright = '2024-%Y, Natalia Kowalska'
author = 'Natalia Kowalska'
version = '0.0.2'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

source_suffix = ".rst"
master_doc = "index"

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.autosectionlabel',
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    'sphinx_rtd_theme',
    'sphinx_changelog',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
suppress_warnings = ['autosectionlabel.*']

# autoapi_modules = {'mymodule': None}
pygments_style = "sphinx"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = 'alabaster'
# html_static_path = ['_static']

# html_theme = "default"
html_theme = "sphinx_rtd_theme"
htmlhelp_basename = "bletcpapp"