
.. module:: pydex

Exceptions
----------
.. currentmodule:: pydex.exc

.. autoexception:: InvalidDalvikHeader
    :members:

----

Containers
----------
Containers refer to the different types of APK files that can be used to store
one or more DEX files. Additionally, PyDex also supports the extraction of
DEX files from container files which may contain one or more APK files within.
PyDex supports the following container types:

- zip: :class:`~pydex.containers.ZipContainer` | :class:`~pydex.containers.InMemoryZipContainer`
- xapk: :class:`~pydex.containers.XAPKContainer` | :class:`~pydex.containers.InMemoryXAPKContainer`
- apks: :class:`~pydex.containers.APKSContainer` | :class:`~pydex.containers.InMemoryAPKSContainer`
- jar: :class:`~pydex.containers.JarContainer`
- apk: :class:`~pydex.containers.APKContainer`

You should use these classes when possible instead of directly using the :class:`~pydex.dalvik.DexFile`
class. The container classes provide a more convenient way to work with DEX
files that come in groups (``classes.dex``, ``classes2.dex``, etc.).

----

.. currentmodule:: pydex.containers

.. autoclass:: Container
    :members:

----

.. autoclass:: InMemoryContainer
    :members:

----

.. autoclass:: DexContainer
    :members:
    :inherited-members:
    :show-inheritance:

----

.. autoclass:: InMemoryDexContainer
    :members:
    :inherited-members:
    :show-inheritance:

----

.. autoclass:: InMemoryZipContainer
    :members:
    :inherited-members:
    :show-inheritance:

----

.. autoclass:: ZipContainer
    :members:
    :inherited-members:
    :show-inheritance:

----

.. autoclass:: InMemoryMultiAPKContainer
    :members:
    :inherited-members:
    :show-inheritance:

----

.. autoclass:: MultiAPKContainer
    :members:
    :inherited-members:
    :show-inheritance:

----

.. autoclass:: InMemoryXAPKContainer
    :members:
    :inherited-members:
    :show-inheritance:

----

.. autoclass:: XAPKContainer
    :members:
    :inherited-members:
    :show-inheritance:

----

.. autoclass:: InMemoryAPKSContainer
    :members:
    :inherited-members:
    :show-inheritance:

----

.. autoclass:: APKSContainer
    :members:
    :inherited-members:
    :show-inheritance:

----

.. autoclass:: JarContainer
    :members:
    :inherited-members:
    :show-inheritance:

----

.. autoclass:: APKContainer
    :members:
    :inherited-members:
    :show-inheritance:

----

Dalvik API
----------
.. currentmodule:: pydex.dalvik

.. autoclass:: DexPool
    :members:

----

.. autoclass:: DexFile
    :members:

----

Dalvik Model API
----------------
The Dalvik Model API provides a way to interact with the different parts of a
DEX file. The Model API consists of low-level classes and high-level classes.
The low-level classes closely follow the structure of the Dalvik executable
format specification. The high-level classes provide a more convenient way to
work with the different parts of a DEX file, abstracting away the complexity of
the low-level classes.

.. seealso::

    `Dalvik Executable Format Specification <https://source.android.com/devices/tech/dalvik/dex-format>`_

----

.. currentmodule:: pydex.dalvik.models

.. autoclass:: DalvikRawItem
    :members:

----

.. autoclass:: DalvikHeader
    :members:
    :show-inheritance:

----

.. autoclass:: DalvikHeaderItem
    :members:

----

.. autoclass:: DalvikStringID
    :members:
    :show-inheritance:

----

.. autoclass:: DalvikStringData
    :members:
    :show-inheritance:

----

.. autoclass:: DalvikStringItem
    :members:

----

.. autoclass:: LazyDalvikString
    :members:

----

.. autoclass:: DalvikTypeID
    :members:
    :show-inheritance:

----

.. autoclass:: DalvikTypeItem
    :members:
