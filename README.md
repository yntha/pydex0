# pydex
Powerful, yet easy to use, python library for loading(and eventually writing) dex files.

[![Documentation Status](https://readthedocs.org/projects/pydex/badge/?version=latest)](https://pydex.readthedocs.io/en/latest/?badge=latest)

## Installation
```bash
python -m pip install --user -U pydex0
```

## Usage
```python
from pydex.dalvik import DexFile

dex = DexFile.from_path("classes.dex")

print(dex.header)
```