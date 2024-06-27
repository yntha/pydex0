# Containers [(source)](https://github.com/yntha/pydex0/blob/master/pydex/containers.py)

This module contains classes that represent the different container files that contain one or more DEX files. The classes in this module are:

- [`Container`](#pydexcontainerscontainerpath-str): Base class for all container classes.
- [`InMemoryContainer`](#pydexcontainersinmemorycontainerdata-bytes): Base class for all container classes that point to an in-memory file-like container.
- [`DexContainer`](#pydexcontainersdexcontainerpath-str): Base class for all container classes that point to a file which contains one or more DEX files.
- [`InMemoryDexContainer`](#pydexcontainersinmemorydexcontainerdata-bytes): Base class for all container classes that point to an in-memory file-like object which contains one or more DEX files.
- [`ZipContainer`](#pydexcontainerszipcontainerpath-str): Class that represents a ZIP file that contains one or more DEX files.
- [`InMemoryZipContainer`](#pydexcontainersinmemoryzipcontainerdata-bytes): Class that represents an in-memory ZIP file that contains one or more DEX files.
- [`MultiAPKContainer`](#pydexcontainersmultiapkcontainerpath-str): Base class that represents a container file which contains one or more APK files. Only the `base` apk is scanned for DEX files.
- [`InMemoryMultiAPKContainer`](#pydexcontainersinmemorymultiapkcontainerdata-bytes): Base class that represents an in-memory container file which contains one or more APK files. Only the `base` apk is scanned for DEX files.
- [`InMemoryXAPKContainer`](#pydexcontainersinmemoryxapkcontainerdata-bytes): Class that represents an in-memory `.xapk` file.
- [`XAPKContainer`](#pydexcontainersxapkcontainerpath-str): Class that represents a `.xapk` file.
- [`InMemoryAPKSContainer`](#pydexcontainersinmemoryapkscontainerdata-bytes): Class that represents an in-memory `.apks` file.
- [`APKSContainer`](#pydexcontainersapkscontainerpath-str): Class that represents a `.apks` file.
- [`JarContainer`](#pydexcontainersjarcontainerpath-str): Class that represents a JAR file.
- [`APKContainer`](#pydexcontainersapkcontainerpath-str): Class that represents an APK file.

## Classes
#### `pydex.containers.Container(path: str)`
Base class that represents a container file(zip, apk, xapk, apks, etc.) which contains either apk files or dex files.


Arguments:

- `path`: The file path to the container file.

-------
[\[top\]](#containers-source)
#### `pydex.containers.InMemoryContainer(data: bytes)`
Base class that represents an in-memory container which contains either apk files or dex files.

Arguments:

- `data`: The bytes object that contains the in-memory container.

-------
[\[top\]](#containers-source)
#### `pydex.containers.DexContainer(path: str)`
Bases: `pydex.containers.Container`

Base class for all container classes that point to a file which contains one or more DEX files.

Arguments:

- `path`: The file path to the container file.

Members:

- `enumerate_dex_files(self) -> Generator[str, None, None]`: Enumerates the DEX files in the container. Must be implemented by subclasses. You should not call this method directly. Use `fetch_dex_files` or `fetch_dex_files_async` instead.

    Returns:

    - A generator that yields the file names of the DEX files in the container.


- `get_dex_data(self, dex_file: str) -> bytes`: Returns the data of the DEX file with the given name. Must be implemented by subclasses. You should not call this method directly. Use `fetch_dex_files` or `fetch_dex_files_async` instead.

    Arguments:

    - `dex_file`: The file name of the DEX file.
    
    Returns:

    - The data of the DEX file.


- `fetch_dex_files(self) -> DexPool`: Collect all the dex files in the container and return a `DexPool` object. Users can then choose to load the `DexFile` objects whenever they want.

    Returns:

    - A `DexPool` object that contains all the DEX files in the container.


- `fetch_dex_files_async(self) -> DexPool`: Asynchronously collect all the dex files in the container and return a `DexPool` object. Users can then choose to load the `DexFile` objects whenever they want.

    Returns:

    - A `DexPool` object that contains all the DEX files in the container.

-------
[\[top\]](#containers-source)
#### `pydex.containers.InMemoryDexContainer(data: bytes)`
Bases: [`pydex.containers.InMemoryContainer`](#pydexcontainersinmemorycontainerdata-bytes)

Base class for all container classes that point to an in-memory file-like object which contains one or more DEX files.

Arguments:

- `data`: The bytes object that contains the in-memory container.

Members:

- `enumerate_dex_files(self) -> Generator[str, None, None]`: Enumerates the DEX files in the container. Must be implemented by subclasses. You should not call this method directly. Use `fetch_dex_files` or `fetch_dex_files_async` instead.

    Returns:

    - A generator that yields the file names of the DEX files in the container.


- `get_dex_data(self, dex_file: str) -> bytes`: Returns the data of the DEX file with the given name. Must be implemented by subclasses. You should not call this method directly. Use `fetch_dex_files` or `fetch_dex_files_async` instead.

    Arguments:

    - `dex_file`: The file name of the DEX file.
    
    Returns:

    - The data of the DEX file.


- `fetch_dex_files(self) -> DexPool`: Collect all the dex files in the container and return a `DexPool` object. Users can then choose to load the `DexFile` objects whenever they want.

    Returns:

    - A `DexPool` object that contains all the DEX files in the container.


- `fetch_dex_files_async(self) -> DexPool`: Asynchronously collect all the dex files in the container and return a `DexPool` object. Users can then choose to load the `DexFile` objects whenever they want.

    Returns:

    - A `DexPool` object that contains all the DEX files in the container.

-------
[\[top\]](#containers-source)
#### `pydex.containers.ZipContainer(path: str)`
Bases: [`pydex.containers.DexContainer`](#pydexcontainersdexcontainerpath-str)

Class that represents a ZIP file that contains one or more DEX files.

Arguments:

- `path`: The file path to the ZIP file.

Members:

- `enumerate_dex_files(self) -> Generator[str, None, None]`: Enumerates the DEX files in the ZIP file. You should not call this method directly. Use `fetch_dex_files` or `fetch_dex_files_async` instead.

    Returns:

    - A generator that yields the file names of the DEX files in the ZIP file.

- `get_dex_data(self, dex_file: str) -> bytes`: Returns the inflated data of the DEX file with the given name. You should not call this method directly. Use `fetch_dex_files` or `fetch_dex_files_async` instead.

    Arguments:

    - `dex_file`: The file name of the DEX file as it appears in the ZIP file.
    
    Returns:

    - The data of the DEX file.

-------
[\[top\]](#containers-source)
#### `pydex.containers.InMemoryZipContainer(data: bytes)`
Bases: [`pydex.containers.InMemoryDexContainer`](#pydexcontainersinmemorydexcontainerdata-bytes)

Class that represents a ZIP file that contains one or more DEX files.

Arguments:

- `path`: The file path to the ZIP file.

Members:

- `enumerate_dex_files(self) -> Generator[str, None, None]`: Enumerates the DEX files in the ZIP file. You should not call this method directly. Use `fetch_dex_files` or `fetch_dex_files_async` instead.

    Returns:

    - A generator that yields the file names of the DEX files in the ZIP file.

- `get_dex_data(self, dex_file: str) -> bytes`: Returns the inflated data of the DEX file with the given name. You should not call this method directly. Use `fetch_dex_files` or `fetch_dex_files_async` instead.

    Arguments:

    - `dex_file`: The file name of the DEX file as it appears in the ZIP file.
    
    Returns:

    - The data of the DEX file.

-------
[\[top\]](#containers-source)
#### `pydex.containers.MultiAPKContainer(path: str)`
Bases: [`pydex.containers.Container`](#pydexcontainerscontainerpath-str)

Base class that represents a container file which contains one or more APK files. Only the `base` apk is scanned for DEX files.

Arguments:

- `path`: The file path to the container file.

Members:

- `get_base_apk(self) -> bytes`: Returns the inflated data of the `base` APK file.

    Returns:

    - The inflated ZIP data of the `base` APK file.

- `fetch_dex_files(self, root_only: bool = True) -> DexPool`: Collect all the dex files in the `base` APK file and return a `DexPool` object. Users can then choose to load the `DexFile` objects whenever they want.

    Arguments:

    - `root_only`: If `True`, only the root directory of the `base` APK file is scanned for DEX files. If `False`, the entire APK file is scanned for DEX files. Default is `True`.

    Returns:

    - A `DexPool` object that contains all the DEX files in the `base` APK file.

- `fetch_dex_files_async(self, root_only: bool = True) -> DexPool`: Asynchronously collect all the dex files in the `base` APK file and return a `DexPool` object. Users can then choose to load the `DexFile` objects whenever they want.

    Arguments:

    - `root_only`: If `True`, only the root directory of the `base` APK file is scanned for DEX files. If `False`, the entire APK file is scanned for DEX files. Default is `True`.

    Returns:

    - A `DexPool` object that contains all the DEX files in the `base` APK file.

-------
[\[top\]](#containers-source)
#### `pydex.containers.InMemoryMultiAPKContainer(data: bytes)`
Bases: [`pydex.containers.InMemoryContainer`](#pydexcontainersinmemorycontainerdata-bytes)

Base class that represents an in-memory container file which contains one or more APK files. Only the `base` apk is scanned for DEX files.

Arguments:

- `data`: The bytes object that contains the container.

Members:

- `get_base_apk(self) -> bytes`: Returns the inflated data of the `base` APK file.

    Returns:
    
    - The inflated ZIP data of the `base` APK file.

- `fetch_dex_files(self, root_only: bool = True) -> DexPool`: Collect all the dex files in the `base` APK file and return a `DexPool` object. Users can then choose to load the `DexFile` objects whenever they want.

    Arguments:

    - `root_only`: If `True`, only the root directory of the `base` APK file is scanned for DEX files. If `False`, the entire APK file is scanned for DEX files. Default is `True`.

    Returns:

    - A `DexPool` object that contains all the DEX files in the `base` APK file.

- `fetch_dex_files_async(self, root_only: bool = True) -> DexPool`: Asynchronously collect all the dex files in the `base` APK file and return a `DexPool` object. Users can then choose to load the `DexFile` objects whenever they want.

    Arguments:

    - `root_only`: If `True`, only the root directory of the `base` APK file is scanned for DEX files. If `False`, the entire APK file is scanned for DEX files. Default is `True`.

    Returns:

    - A `DexPool` object that contains all the DEX files in the `base` APK file.

-------
[\[top\]](#containers-source)
#### `pydex.containers.InMemoryXAPKContainer(data: bytes)`
Bases: [`pydex.containers.InMemoryMultiAPKContainer`](#pydexcontainersinmemorymultiapkcontainerdata-bytes)

Class that represents an in-memory `.xapk` file. `.xapk` files are zip files that contain numerous apk files for different architectures, locales, and screen densities, among the `base` apk. The `base` apk is typically the apk file that contains a package name for the file name. Among the contents of the container, there exists a `manifest.json` file that contains metadata about the container, including the file name of the `base` apk.

Arguments:

- `data`: The bytes object that contains the in-memory `.xapk` file.

Members:

- `get_base_apk(self) -> bytes`: Parses the `.xapk`'s `manifest.json` file to identify and return the inflated data of the `base` APK file.

    Returns:

    - The inflated ZIP data of the `base` APK file.
    
    Raises:

    - `FileNotFoundError`: If the `manifest.json` file is not found in the container.
    - `ValueError`: If the `base` apk file is not found in the manifest file.

-------
[\[top\]](#containers-source)
#### `pydex.containers.XAPKContainer(path: str)`
Bases: [`pydex.containers.MultiAPKContainer`](#pydexcontainersmultiapkcontainerpath-str)

Class that represents an `.xapk` file. `.xapk` files are zip files that contain numerous apk files for different architectures, locales, and screen densities, among the `base` apk. The `base` apk is typically the apk file that contains a package name for the file name. Among the contents of the container, there exists a `manifest.json` file that contains metadata about the container, including the file name of the `base` apk.

Arguments:

- `path`: The file path to the `.xapk` file.

Members:

- `get_base_apk(self) -> bytes`: Parses the `.xapk`'s `manifest.json` file to identify and return the inflated data of the `base` APK file.

    Returns:

    - The inflated ZIP data of the `base` APK file.
    
    Raises:

    - `FileNotFoundError`: If the `manifest.json` file is not found in the container.
    - `ValueError`: If the `base` apk file is not found in the manifest file.

-------
[\[top\]](#containers-source)
#### `pydex.containers.InMemoryAPKSContainer(data: bytes)`
Bases: [`pydex.containers.InMemoryMultiAPKContainer`](#pydexcontainersinmemorymultiapkcontainerdata-bytes)

Class that represents an in-memory `.apks` file. `.apks` files are zip files that contain numerous apk files for specific architectures, locales, and screen densities, among the `base` apk.

Arguments:

- `data`: The bytes object that contains the in-memory `.apks` file.

Members:

- `get_base_apk(self) -> bytes`: Identifies and returns the inflated data of the `base` APK file based on it's name `base.apk`.

    Returns:

    - The inflated ZIP data of the `base` APK file.

    Raises:

    - `FileNotFoundError`: If the `manifest.json` file is not found in the container.
    - `ValueError`: If the `base` apk file is not found in the manifest file.

-------
[\[top\]](#containers-source)
#### `pydex.containers.APKSContainer(path: str)`
Bases: [`pydex.containers.MultiAPKContainer`](#pydexcontainersmultiapkcontainerpath-str)

Class that represents an `.apks` file. `.apks` files are zip files that contain numerous apk files for specific architectures, locales, and screen densities, among the `base` apk.

Arguments:

- `path`: The file path to the `.apks` file.

Members:

- `get_base_apk(self) -> bytes`: Identifies and returns the inflated data of the `base` APK file based on it's name `base.apk`.

    Returns:

    - The inflated ZIP data of the `base` APK file.

    Raises:

    - `FileNotFoundError`: If the `manifest.json` file is not found in the container.
    - `ValueError`: If the `base` apk file is not found in the manifest file.

-------
[\[top\]](#containers-source)
#### `pydex.containers.JarContainer(path: str)`
Bases: [`pydex.containers.DexContainer`](#pydexcontainersdexcontainerpath-str)

Class that represents a JAR file. JAR files are zip files that contain Java class files, however, `dx` may convert them to DEX files while retaining the `.jar` extension and format.

Arguments:

- `path`: The file path to the JAR file.

-------
[\[top\]](#containers-source)
#### `pydex.containers.APKContainer(path: str)`
Bases: [`pydex.containers.ZipContainer`](#pydexcontainerszipcontainerpath-str)

Class that represents an APK file. APK files are zip files that contain Android application files, resource files, and DEX files.

Arguments:

- `path`: The file path to the APK file.
