from __future__ import annotations

import asyncio
import io
import zipfile
import pathlib
import json

from collections.abc import Generator

from pydex.dalvik.executable import DexPool, DexFile


class Container:
    """
    A class that represents a container file(zip, apk, xapk, apks, etc.) which
    contains either apk files or dex files.
    """

    def __init__(self, path: str):
        self.path = pathlib.Path(path)


class InMemoryContainer:
    """
    A class that represents an in-memory container which contains either apk
    files or dex files.
    """

    def __init__(self, data: bytes):
        self.data = data


class DexContainer(Container):
    """
    A class that represents a container file(zip, apk, jar) which
    contains dex files.
    """

    def __init__(self, path: str):
        super().__init__(path)

    def enumerate_dex_files(self) -> Generator[str, None, None]:
        """
        Enumerate the dex files in the container file.
        """

        raise NotImplementedError()

    def get_dex_data(self, dex_file: str) -> bytes:
        """
        Get the data of the dex file.
        """

        raise NotImplementedError()

    def fetch_dex_files(self) -> DexPool:
        """
        Lazily load the dex files in the container file.
        """

        return DexPool([DexFile(self.get_dex_data(dex_file)) for dex_file in self.enumerate_dex_files()])

    async def fetch_dex_files_async(self) -> DexPool:
        """
        Lazily load the dex files in the container file asynchronously.

        Returns: A DexPool object containing the dex files.
        """

        return await asyncio.to_thread(self.fetch_dex_files)


class InMemoryDexContainer(InMemoryContainer):
    """
    A class that represents a container file(zip, apk, jar) which
    contains dex files.
    """

    def __init__(self, data: bytes):
        super().__init__(data)

    def enumerate_dex_files(self) -> Generator[str, None, None]:
        """
        Enumerate the dex files in the container file.
        """

        raise NotImplementedError()

    def get_dex_data(self, dex_file: str) -> bytes:
        """
        Get the data of the dex file.
        """

        raise NotImplementedError()

    def fetch_dex_files(self) -> DexPool:
        """
        Lazily load the dex files in the container file.
        """

        return DexPool([DexFile(self.get_dex_data(dex_file)) for dex_file in self.enumerate_dex_files()])

    async def fetch_dex_files_async(self) -> DexPool:
        """
        Lazily load the dex files in the container file asynchronously.

        Returns: A DexPool object containing the dex files.
        """

        return await asyncio.to_thread(self.fetch_dex_files)


class InMemoryZipContainer(InMemoryDexContainer):
    """
    A class that represents an in-memory zip file which contains one or more
    dex files.

    Parameters:
        - data: bytes: The zip file data.
        - root_only: bool: If True, only the root files in the archive will be
            considered.
    """

    def __init__(self, data: bytes, root_only: bool = False):
        self.root_only = root_only

        super().__init__(data)

    def enumerate_dex_files(self) -> Generator[str, None, None]:
        with zipfile.ZipFile(io.BytesIO(self.data), "r") as zip_file:
            for file in zip_file.namelist():
                file: pathlib.Path = pathlib.Path(file)

                if self.root_only:
                    if file.parent.name != "":
                        continue

                    if file.suffix == ".dex":
                        yield file.name

                    continue

                if file.suffix == ".dex":
                    yield file.name

    def get_dex_data(self, dex_file: str) -> bytes:
        with zipfile.ZipFile(io.BytesIO(self.data), "r") as zip_file:
            with zip_file.open(dex_file, "r") as file:
                return file.read()


class ZipContainer(DexContainer):
    """
    A class that represents a zip file which contains one or more dex files.

    Parameters:
        - path: str: The path to the zip file.
        - root_only: bool: If True, only the root files in the archive will be
            considered.
    """

    def __init__(self, path: str, root_only: bool = False):
        self.root_only = root_only
        self.internal_container = InMemoryZipContainer(pathlib.Path(path).read_bytes())

        super().__init__(path)

    def enumerate_dex_files(self) -> Generator[str, None, None]:
        return self.internal_container.enumerate_dex_files()

    def get_dex_data(self, dex_file: str) -> bytes:
        return self.internal_container.get_dex_data(dex_file)


class InMemoryMultiAPKContainer(InMemoryContainer):
    """
    A class that represents an in-memory apk container which contains one or
    more apk files.

    Parameters:
        - data: bytes: The apk container file data.
    """

    def __init__(self, data: bytes):
        super().__init__(data)

    def get_base_apk(self) -> bytes:
        """
        Get the base apk file as a bytes object.
        """

        raise NotImplementedError()

    def fetch_dex_files(self, root_only: bool = False) -> DexPool:
        """
        Lazily load the dex files in the base apk file.

        Parameters:
            - root_only: bool: If True, only the root files in the archive will
                be considered.

        Returns: A DexPool object containing the dex files.
        """

        zip_container = InMemoryZipContainer(self.get_base_apk(), root_only)

        return zip_container.fetch_dex_files()

    async def fetch_dex_files_async(self, root_only: bool = False) -> DexPool:
        """
        Lazily load the dex files in the base apk file asynchronously.

        Parameters:
            - root_only: bool: If True, only the root files in the archive will
                be considered.

        Returns: A DexPool object containing the dex files.
        """

        return await asyncio.to_thread(self.fetch_dex_files, root_only)


class MultiAPKContainer(Container):
    """
    A class that represents a container file which contains one or more apk
    files.

    Parameters:
        - path: str: The path to the apk container file.
    """

    def __init__(self, path: str):
        super().__init__(path)

    def get_base_apk(self) -> bytes:
        """
        Get the base apk file as a bytes object.
        """

        raise NotImplementedError()

    def fetch_dex_files(self, root_only: bool = False) -> DexPool:
        """
        Lazily load the dex files in the base apk file.

        Parameters:
            - root_only: bool: If True, only the root files in the archive will
                be considered.

        Returns: A DexPool object containing the dex files.
        """

        zip_container = InMemoryZipContainer(self.get_base_apk(), root_only)

        return zip_container.fetch_dex_files()

    async def fetch_dex_files_async(self, root_only: bool = False) -> DexPool:
        """
        Lazily load the dex files in the base apk file asynchronously.

        Parameters:
            - root_only: bool: If True, only the root files in the archive will
                be considered.

        Returns: A DexPool object containing the dex files.
        """

        return await asyncio.to_thread(self.fetch_dex_files, root_only)


class InMemoryXAPKContainer(InMemoryMultiAPKContainer):
    """
    A class that represents an in-memory xapk container file which contains one
    or more apk files.

    Parameters:
        - data: bytes: The xapk container file data.
    """

    def __init__(self, data: bytes):
        super().__init__(data)

    def get_base_apk(self) -> bytes:
        with zipfile.ZipFile(io.BytesIO(self.data), "r") as zip_file:
            for file in zip_file.namelist():
                file: pathlib.Path = pathlib.Path(file)

                if file.name != "manifest.json":
                    continue

                with zip_file.open(str(file), "r") as manifest_file:
                    manifest = json.load(manifest_file)

                    for split_apk in manifest["split_apks"]:
                        if split_apk["id"] != "base":
                            continue

                        with zip_file.open(split_apk["file"], "r") as base_apk_file:
                            return base_apk_file.read()
                    else:
                        raise ValueError("Base apk not found in manifest file.")
            else:
                raise FileNotFoundError("Manifest file not found in xapk file.")


class XAPKContainer(MultiAPKContainer):
    """
    A class that represents a xapk file which contains one or more apk files.
    These conatiner files contain various apk files, whose purpose is noted in
    the `manifest.json` file.

    Parameters:
        - path: str: The path to the xapk file.
    """

    def __init__(self, path: str):
        super().__init__(path)

    def get_base_apk(self) -> bytes:
        return InMemoryXAPKContainer(pathlib.Path(self.path).read_bytes()).get_base_apk()


class InMemoryAPKSContainer(InMemoryMultiAPKContainer):
    """
    A class that represents an in-memory apks container file which contains one
    or more apk files.

    Parameters:
        - data: bytes: The apks container file data.
    """

    def __init__(self, data: bytes):
        super().__init__(data)

    def get_base_apk(self) -> bytes:
        with zipfile.ZipFile(io.BytesIO(self.data), "r") as zip_file:
            for file in zip_file.namelist():
                file: pathlib.Path = pathlib.Path(file)

                if file.name != "base.apk":
                    continue

                with zip_file.open(str(file), "r") as base_apk_file:
                    return base_apk_file.read()
            else:
                raise FileNotFoundError("Base apk not found in apks file.")


class APKSContainer(MultiAPKContainer):
    """
    A class that represents an apks file which contains one or more apk files.
    This is also known as a split-apk.

    Parameters:
        - path: str: The path to the apks file.
    """

    def __init__(self, path: str):
        super().__init__(path)

    def get_base_apk(self) -> bytes:
        return InMemoryAPKSContainer(pathlib.Path(self.path).read_bytes()).get_base_apk()


class JarContainer(ZipContainer):
    """
    A class that represents a jar file which contains one or more dex files.

    Parameters:
        - path: str: The path to the jar file.
    """

    def __init__(self, path: str):
        super().__init__(path)


class APKContainer(ZipContainer):
    """
    A class that represents an apk file which contains one or more dex files.
    Only the root files in the archive will be considered.

    Parameters:
        - path: str: The path to the apk file.
    """

    def __init__(self, path: str):
        super().__init__(path, root_only=True)
