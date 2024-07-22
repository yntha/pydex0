Welcome to PyDex's documentation!
=================================

PyDex is a Python library for the analysis and instrumentation of Android/Dalvik bytecode. It is designed to on par with `Ben Gruver's <https://github.com/JesusFreke>`_ `dexlib2 <https://github.com/JesusFreke/smali/tree/master/dexlib2>`_ project. `PyDex is a work in progress and is not yet ready for production use.`

PyDex provides both a high-level and low-level API for interacting with Android/Dalvik bytecode. The high-level API is designed to be easy to use and abstracts away the details of the low-level API. The low-level API is designed to be more flexible and provide more control over the bytecode. The low-level API closely follows the `Dalvik executable format <https://source.android.com/docs/core/runtime/dex-format>`_.

.. toctree::
   :maxdepth: 2
   :caption: Table of Contents:

   api

Installation
------------
PyDex can be installed using pip:

.. code-block:: bash

    python -m pip install --user -U pydex0

Unfortunately, PyDex is named `pydex0` on PyPI because the name `pydex` was already taken.

.. image:: _static/firedroid.png
    :alt: FireDroid
    :align: center
