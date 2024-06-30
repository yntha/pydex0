# Dalvik [(source)](https://github.com/yntha/pydex0/blob/master/pydex/dalvik/__init__.py)

This module contains classes for parsing and representing various Dalvik structures. The primary class of focus is `DexFile`, which is used to load and represent a DEX file. The following classes are defined in this module:

- [`DexFile`](#pydexdalvikdexfiledata-bytes): Represents a DEX file. Can be loaded from a bytes object or a file path.
- [`DexPool`](): Represents a collection of DEX files. A DexPool is returned by the [container]() class functions.


## Classes
[\[top\]](#dalvik-source)
#### `pydex.dalvik.DexFile(data: bytes)`

Represents a DEX file. Can be loaded from a bytes object or a file path if you use the [`from_path`](#dexfile-from_path) class method. This class is built to load DEX files lazily, or asynchronously. It parses a DEX file into low-level models and high-level models that are available as attributes. Only the high-level models are available as attributes to a `DexFile` instance, so to access the low-level models, simply access the `raw_item` attribute of any high-level item. For example:
```
>>> dex = DexFile(data)
>>> lazy_string: LazyDalvikString = dex.get_string_by_id(0)
>>> string_item: DalvikStringItem = lazy_string.load()  # DalvikStringItem is the high-level model here
>>> string_item.raw_item.utf16_size  # access the lower-level model attributes
4
```


Arguments:

- `data` || `bytes`: Bytes object representing a DEX file.

Attributes:

- `data` || `bytes`: <a id="dexfile-data"></a> The original, unmodified, DEX file data.
- `stream` || [`DeserializingStream`](): <a id="dexfile-stream"></a> The backend stream that handles the reading of binary data. It is a [`DeserializingStream`]() that has been initialized with the byte order set to [`ByteOrder.LITTLE_ENDIAN`]().
- `header` || [`DalvikHeaderItem`](): <a id="dexfile-header"></a> The high-level DEX file header model. It should never be `None` as it is the first model that gets processed when the `DexFile` constructor runs.
- `strings` || `list` of [`LazyDalvikString`]() | [`DalvikStringItem`](): <a id="dexfile-strings"></a> List of all the dalvik strings in this `DexFile`. This list is primarily composed of [`LazyDalvikString`]() models when you use [`parse_dex`](#dexfile-parse_dex), however, if you use [`load_all_strings`](#dexfile-load_all_strings), this list will be composed of loaded [`DalvikStringItem`]() models.


Members:

- *`classmethod`* `from_path(cls, path: str) -> DexFile`: <a id="dexfile-from_path"></a> Creates a `DexFile` instance from a file path.

    Arguments:

    - `path` || `str`: The file path to the DEX file.

    Returns: A new `DexFile` instance created from this file.


- `parse_dex_prologue(self) -> DexFile`: <a id="dexfile-parse_dex_prologue"></a> Helper function that does misc startup tasks for parsing the dex file.

    Raises:

    - `ValueError`: If the [`endian_tag`]() field of the DEX header is invalid.

    Returns: The current `DexFile` instance (`self`).


- `parse_dex(self) -> DexFile`: <a id="dexfile-parse_dex"></a> Parse the DEX file. This function will attempt to entirely parse this DEX file in one go and fill in all the uninitialized class attributes.

    Returns: The current `DexFile` instance (`self`).


- `parse_header(self) -> DalvikHeaderItem`: <a id="dexfile-parse_header"></a> This function parses the DEX header. Additionally, this function also performs a few checks to ensure file integrity.

    Raises:

    - `ValueError`: If the first 4 bytes don't match `dex\0xA`.
    - `ValueError`: If byte 8 is not a null byte. This null byte terminates the DEX magic number, and according to the docs, exists to ensure the file isn't corrupted.
    - `ValueError`: If the parsed checksum does not equal to the calculated adler32 checksum of the rest of the file.
    - `ValueError`: If [`header_size`]() is not `0x70`. This is a constant value, and should be constant across all DEX files unless specified by the specification.
    - `ValueError`: If [`type_ids_size`]() is greater than or equal to `0xFFFF`.
    - `ValueError`: If [`proto_ids_size`]() is greater than or equal to `0xFFFF`.
    - `ValueError`: If [`data_size`]() is not a multiple of `sizeof(uint)`.

    Returns: A newly constructed [`DalvikHeaderItem`]() model instance for this DEX file.


- `async parse_header_async(self) -> DalvikHeaderItem`: <a id="dexfile-parse_header_async"></a> This function asynchronously parses the DEX header. Additionally, this function also performs a few checks to ensure file integrity.

    Raises:

    - `ValueError`: If the first 4 bytes don't match `dex\0xA`.
    - `ValueError`: If byte 8 is not a null byte. This null byte terminates the DEX magic number, and according to the docs, exists to ensure the file isn't corrupted.
    - `ValueError`: If the parsed checksum does not equal to the calculated adler32 checksum of the rest of the file.
    - `ValueError`: If [`header_size`]() is not `0x70`. This is a constant value, and should be constant across all DEX files unless specified by the specification.
    - `ValueError`: If [`type_ids_size`]() is greater than or equal to `0xFFFF`.
    - `ValueError`: If [`proto_ids_size`]() is greater than or equal to `0xFFFF`.
    - `ValueError`: If [`data_size`]() is not a multiple of `sizeof(uint)`.

    Returns: A newly constructed [`DalvikHeaderItem`]() model instance for this DEX file.


- `parse_strings(self) -> list[LazyDalvikString]`: <a id="dexfile-parse_strings"></a> This function collects all the dalvik string items in this DEX file and returns them as a list of [`LazyDalvikString`](). A clone stream is used so to not alter the DEX file stream.

    Returns: A list of [`LazyDalvikString`]() models.


- `async parse_strings_async(self) -> list[LazyDalvikString]`: <a id="dexfile-parse_strings_async"></a> This function asynchronously collects all the dalvik string items in this DEX file and returns them as a list of [`LazyDalvikString`](). A clone stream is used so to not alter the DEX file stream.

    Returns: A list of [`LazyDalvikString`]() models.


- `load_all_strings(self) -> list[DalvikStringItem]`: <a id="dexfile-load_all_strings"></a> This function invokes the [`load()`]() function for all the lazy dalvik strings in the [`strings`](#dexfile-strings) attribute. It will also convert every model in [`strings`](#dexfile-strings) to a loaded `DalvikStringItem` model.

    Returns: A list of [`DalvikStringItem`]() models.


- `async load_all_strings(self) -> list[DalvikStringItem]`: <a id="dexfile-load_all_strings_async"></a> This function will asynchronously invoke the [`load()`]() function for all the lazy dalvik strings in the [`strings`](#dexfile-strings) attribute. It will also convert every model in [`strings`](#dexfile-strings) to a loaded `DalvikStringItem` model.

    Returns: A list of [`DalvikStringItem`]() models.


- `get_string_by_id(self, string_id: int) -> LazyDalvikString`: <a id="dexfile-get_string_by_id"></a> Get a dalvik string by its id. The difference between this, and `dex.strings[id]` is that this method does not require all the strings to be collected from the dex file. This method is useful when you only need a single string from the dex file and don't want to load the entire dex file with [`parse_dex`](#dexfile-parse_dex).

    Arguments:

    - `string_id` || `int`: The numerical string ID to fetch. String IDs are 0-indexed.

    Raises:

    - `ValueError`: If `string_id` is out of range.

    Returns: A [`LazyDalvikString`]() model instance.

-------
[\[top\]](#dalvik-source)
#### `pydex.dalvik.DexPool:`
Represents a collection of DEX files. A DexPool is returned by the [container]() class functions. In the future, DexPools will have functions that allow you to operate and transform classes across the multiple DEX files of a container.

Attributes:

- `dex_files` || `list` of [`DexFile`](#pydexdalvikdexfiledata-bytes): The list of [`DexFile`](#pydexdalvikdexfiledata-bytes) instances in this pool.
