<div align="center" style="margin: 25px;">
<img height="100px" src="https://raw.githubusercontent.com/yntha/pydex0/master/source/_static/logo.png"/>
</div>

# PyDex
Powerful, yet easy to use, python library for loading(and eventually writing) dex files.

[![PyPI - Version](https://img.shields.io/pypi/v/pydex0)](https://pypi.org/project/pydex0/)
[![Python application](https://github.com/yntha/pydex0/actions/workflows/run-tests.yml/badge.svg)](https://github.com/yntha/pydex0/actions/workflows/run-tests.yml)
[![Documentation Status](https://readthedocs.org/projects/pydex/badge/?version=latest)](https://pydex.readthedocs.io/en/latest/?badge=latest)

PyDex is a Python library for the analysis and instrumentation of Android/Dalvik bytecode. It is designed to on par with [Ben Gruver's](https://github.com/JesusFreke>) [`dexlib2`](https://github.com/JesusFreke/smali/tree/master/dexlib2) project. *PyDex is a work in progress and is not yet ready for production use.*

PyDex provides both a high-level and low-level API for interacting with Android/Dalvik bytecode. The high-level API is designed to be easy to use and abstracts away the details of the low-level API. The low-level API is designed to be more flexible and provide more control over the bytecode. The low-level API closely follows the [Dalvik executable format](https://source.android.com/docs/core/runtime/dex-format)

### Installation
PyDex can be installed using pip:
```bash
    python -m pip install --user -U pydex0
```

Unfortunately, PyDex is named *pydex0* on PyPI because the name *pydex* was already taken.

---

<div align="center">
<img height="100px" src="https://raw.githubusercontent.com/yntha/pydex0/master/source/_static/firedroid.png"/>
</div>