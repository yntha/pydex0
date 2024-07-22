# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import sys
import os

sys.path.insert(0, '../')

project = 'pydex'
copyright = '2024, yntha'
author = 'yntha'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon', "sphinx_new_tab_link", "myst_parser", "sphinxext.opengraph"]
templates_path = ['_templates']
exclude_patterns = []

autodoc_member_order = 'bysource'
autodoc_class_signature = 'separated'
autodoc_typehints = 'signature'
autodoc_inherit_docstrings = True
# autodoc_preserve_defaults = True

new_tab_link_show_external_link_icon = True

myst_enable_extensions = [
    "colon_fence",
    "html_admonition",
]

ogp_image = "https://raw.githubusercontent.com/yntha/pydex0/master/source/_static/og_logo.png"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'shibuya'
html_static_path = ['_static']
html_theme_options = {
    'github_url': "https://github.com/yntha/pydex0",
    "discussion_url": "https://github.com/yntha/pydex0/discussions",
    "og_image_url": "_static/og_logo.png",
    "accent_color": "grass",
    "dark_code": True,
}
html_title = "PyDex Docs"
html_logo = "_static/logo.png"
html_favicon = "_static/favicon.svg"
