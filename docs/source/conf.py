#!/usr/bin/env python
# docs/source/conf.py

"""
..

===============================================================================
    Copyright (C) 2012-2018 Rudolf Cardinal (rudolf@pobox.com).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
===============================================================================

Sphinx configuration file
"""
import os
import sys

import logging
from typing import Any, Callable, Dict, List, Tuple

from cardinal_pythonlib.logs import (
    BraceStyleAdapter,
    main_only_quicksetup_rootlogger,
)
from docutils import nodes
from docutils.nodes import Element, Node
from docutils.parsers.rst.roles import register_canonical_role
from docutils.parsers.rst.states import Inliner
from sphinx.application import Sphinx

from camcops_server.cc_modules.cc_version import CAMCOPS_SERVER_VERSION_STRING

log = BraceStyleAdapter(logging.getLogger(__name__))


# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

THIS_DIR = os.path.dirname(os.path.realpath(__file__))  # .../docs/source
CAMCOPS_ROOT_DIR = os.path.abspath(os.path.join(THIS_DIR, os.pardir, os.pardir))  # .../  # noqa
CAMCOPS_SERVER_ROOT_DIR = os.path.join(CAMCOPS_ROOT_DIR, "server")

sys.path.insert(0, CAMCOPS_SERVER_ROOT_DIR)


# -- Project information -----------------------------------------------------

project = 'CamCOPS'
# noinspection PyShadowingBuiltins
copyright = '2012-2018, Rudolf Cardinal'
author = 'Rudolf Cardinal'

# The short X.Y version
version = CAMCOPS_SERVER_VERSION_STRING
# The full version, including alpha/beta/rc tags
release = CAMCOPS_SERVER_VERSION_STRING


# -- General configuration ---------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.githubpages',
    'sphinx.ext.imgmath',
    'sphinx.ext.napoleon',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path .
exclude_patterns = [
    "client/include*.rst",
    "server/include*.rst",
    "tasks/include*.rst",
    # not "**/include*.rst", as that would hit some of the tablet_qt files
]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#

# See http://www.sphinx-doc.org/en/master/theming.html
# html_theme = 'alabaster'  # elegant but monochrome
# html_theme = 'classic'  # like the Python docs. GOOD.
# html_theme = 'sphinxdoc'  # OK; TOC on right
# html_theme = 'scrolls'  # ugly
# html_theme = 'agogo'  # nice, but a bit big-print; TOC on right; justified
# html_theme = 'traditional'  # moderately ugly
html_theme = 'nature'  # very nice. CHOSEN.
# html_theme = 'haiku'  # dosen't do sidebar
# html_theme = 'pyramid'  # Once inline code customized, GOOD.
# html_theme = 'bizstyle'  # OK

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
# html_theme_options = {}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# The default sidebars (for documents that don't match any pattern) are
# defined by theme itself.  Builtin themes are using these templates by
# default: ``['localtoc.html', 'relations.html', 'sourcelink.html',
# 'searchbox.html']``.
#
# html_sidebars = {}

# https://stackoverflow.com/questions/18969093/how-to-include-the-toctree-in-the-sidebar-of-each-page
html_sidebars = {
    '**': ['globaltoc.html', 'relations.html', 'sourcelink.html',
           'searchbox.html']
}


# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'CamCOPSdoc'


# -- Options for LaTeX output ------------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',

    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',
    # RNC:
    #     'preamble': """
    # \usepackage[utf8]{inputenc}
    #     """,

    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'CamCOPS.tex', 'CamCOPS Documentation',
     'Rudolf Cardinal', 'manual'),
]


# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'camcops', 'CamCOPS Documentation',
     [author], 1)
]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'CamCOPS', 'CamCOPS Documentation',
     author, 'CamCOPS', 'Cambridge Cognitive and Psychiatric Assessment Kit.',
     'Miscellaneous'),
]


# -- Extension configuration -------------------------------------------------

# http://www.sphinx-doc.org/en/master/ext/todo.html
todo_include_todos = True


# -----------------------------------------------------------------------------
# Setup function
# -----------------------------------------------------------------------------

def setup(app: Sphinx) -> None:
    # Add CSS
    # - https://stackoverflow.com/questions/23462494/how-to-add-a-custom-css-file-to-sphinx  # noqa
    app.add_stylesheet('css/camcops_docs.css')  # may also be an URL


# -----------------------------------------------------------------------------
# Add CSS
# -----------------------------------------------------------------------------

# html_context = {
#     'css_files': ['_static/css/camcops_docs.css'],
# }


RoleFuncReturnType = Tuple[List[Node], List[str]]
RoleFuncType = Callable[
    [str, str, str, int, Inliner, Dict[str, Any], List[str]],
    RoleFuncReturnType
]


def register_css_role_allowing_content_substitution(css_class: str) -> None:
    """
    If you create a role in RST like this:

        .. role:: somecssclass

    then you can use it like this:

        :somecssclass:`here is my content`

    ... and it will render (after some CSS class name alterations, like
    converting underscores to minus) as:

        <span class="somecssclass">here is my content</span

    However, you can't also use substitutions in the content. For example, if
    you have defined a substitution

        .. |biohazard| image:: biohazard_symbole.png
           :height: 24px
           :width: 24px

    then you can use that substitution as

        Always apply a |biohazard| sticker in the presence of biohazards.

    but not as

        :somecssclass:`Beware the poison! |biohazard| Beware!`

    This function registers a role under the name of that CSS class, so now you
    can.
    """
    def rolefunc(role_name: str,  # e.g. "role"
                 rawtext: str,  # e.g. ":role:`text`"
                 text: str,  # e.g. "text"
                 lineno: int,
                 inliner: Inliner,
                 options: Dict[str, Any] = None,
                 content: List[str] = None) -> Tuple[List[Node], List[str]]:
        """
        Attempt to implemented substitutions inside inline markup.
        This is not directly supported:
            https://sourceforge.net/p/docutils/feature-requests/53/
        Role functions: see
            http://docutils.sourceforge.net/docs/howto/rst-roles.html
        See also:
            https://github.com/sphinx-doc/sphinx/issues/2173
        Returns the tuple (nodes, messages).
        Search docutils for "role_fn" to see how this function will be called.
        """
        options = options or {}  # type: Dict[str, Any]
        content = content or []  # type: List[str]
        log.debug(
            "rolefunc() called with role_name={rn!r}, rawtext={rt!r}, "
            "text={t!r}, lineno={ln}, inliner={i!r}, "
            "options={o!r}, content={c!r}".format(
                rn=role_name, rt=rawtext, t=text,
                ln=lineno, i=inliner, o=options, c=content))
        parsed_nodes, parsed_msgs = inliner.parse(
            text=text,
            lineno=0,
            memo=inliner,
            parent=None,
        )  # type: Tuple[List[Node], List[str]]
        top_node = nodes.inline(  # was nodes.inline
            text="",
            refid=css_class,
            **options
        )  # type: Element
        top_node['classes'].append(css_class)  # see deprecated Element.set_class  # noqa
        top_node += parsed_nodes  # adds children to this_node; see Element
        return [top_node], []

    register_canonical_role(css_class, rolefunc)


main_only_quicksetup_rootlogger(level=logging.INFO)

register_css_role_allowing_content_substitution("tabletmenu")

# https://stackoverflow.com/questions/5599254/how-to-use-sphinxs-autodoc-to-document-a-classs-init-self-method  # noqa
autoclass_content = "both"

# To prevent Alembic env.py breaking:
os.environ["_SPHINX_AUTODOC_IN_PROGRESS"] = "true"
