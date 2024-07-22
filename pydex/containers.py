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
        #: The path to the container file.
        self.path: pathlib.Path = pathlib.Path(path)


class InMemoryContainer:
    """
    A class that represents an in-memory container which contains either apk
    files or dex files.
    """

    def __init__(self, data: bytes):
        #: The data of the container file.
        self.data: bytes = data


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

        Returns:
            A generator that yields the dex filepaths in the container file.
        """

        raise NotImplementedError()

    def get_dex_data(self, dex_file: str) -> bytes:
        """
        Get the data of the dex file.

        Parameters:
            str dex_file: The filepath of the dex file in the container file.

        Returns:
            The data of the dex file within the container.
        """

        raise NotImplementedError()

    def fetch_dex_files(self) -> DexPool:
        """
        Lazily load the dex files in the container file.

        Returns:
            A DexPool object containing the dex files.
        """

        return DexPool([DexFile(self.get_dex_data(dex_file)) for dex_file in self.enumerate_dex_files()])

    async def fetch_dex_files_async(self) -> DexPool:
        """
        Lazily load the dex files in the container file asynchronously.

        Returns:
            A DexPool object containing the dex files.
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

        Returns:
            A generator that yields the dex filepaths in the container file.
        """

        raise NotImplementedError()

    def get_dex_data(self, dex_file: str) -> bytes:
        """
        Get the data of the dex file.

        Parameters:
            str dex_file: The filepath of the dex file in the container file.

        Returns:
            The data of the dex file within the container.
        """

        raise NotImplementedError()

    def fetch_dex_files(self) -> DexPool:
        """
        Lazily load the dex files in the container file.

        Returns:
            A DexPool object containing the dex files.
        """

        return DexPool([DexFile(self.get_dex_data(dex_file)) for dex_file in self.enumerate_dex_files()])

    async def fetch_dex_files_async(self) -> DexPool:
        """
        Lazily load the dex files in the container file asynchronously.

        Returns:
            A DexPool object containing the dex files.
        """

        return await asyncio.to_thread(self.fetch_dex_files)


class InMemoryZipContainer(InMemoryDexContainer):
    """
    A class that represents an in-memory zip file which contains one or more
    dex files.

    Parameters:
        bytes data: The zip file data.
        bool root_only: If True, only the root files in the archive will be
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
        str path: The path to the zip file.
        bool root_only: If True, only the root files in the archive will be
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
        bytes data: The apk container file data.
    """

    def __init__(self, data: bytes):
        super().__init__(data)

    def get_base_apk(self) -> bytes:
        """
        Get the base apk file as a bytes object.

        Returns:
            The file data of the base apk file in the container.
        """

        raise NotImplementedError()

    def fetch_dex_files(self, root_only: bool = False) -> DexPool:
        """
        Lazily load the dex files in the base apk file.

        Parameters:
            bool root_only: If True, only the root files in the archive will
                be considered.

        Returns:
            A DexPool object containing the dex files.
        """

        zip_container = InMemoryZipContainer(self.get_base_apk(), root_only)

        return zip_container.fetch_dex_files()

    async def fetch_dex_files_async(self, root_only: bool = False) -> DexPool:
        """
        Lazily load the dex files in the base apk file asynchronously.

        Parameters:
            bool root_only: If True, only the root files in the archive will
                be considered.

        Returns:
            A DexPool object containing the dex files.
        """

        return await asyncio.to_thread(self.fetch_dex_files, root_only)


class MultiAPKContainer(Container):
    """
    A class that represents a container file which contains one or more apk
    files.

    Parameters:
        str path: The path to the apk container file.
    """

    def __init__(self, path: str):
        super().__init__(path)

    def get_base_apk(self) -> bytes:
        """
        Get the base apk file as a bytes object.

        Returns:
            The file data of the base apk file in the container
        """

        raise NotImplementedError()

    def fetch_dex_files(self, root_only: bool = False) -> DexPool:
        """
        Lazily load the dex files in the base apk file.

        Parameters:
            bool root_only: If True, only the root files in the archive will
                be considered.

        Returns:
            A DexPool object containing the dex files.
        """

        zip_container = InMemoryZipContainer(self.get_base_apk(), root_only)

        return zip_container.fetch_dex_files()

    async def fetch_dex_files_async(self, root_only: bool = False) -> DexPool:
        """
        Lazily load the dex files in the base apk file asynchronously.

        Parameters:
            bool root_only: If True, only the root files in the archive will
                be considered.

        Returns:
            A DexPool object containing the dex files.
        """

        return await asyncio.to_thread(self.fetch_dex_files, root_only)


class InMemoryXAPKContainer(InMemoryMultiAPKContainer):
    """
    A class that represents an in-memory xapk container file which contains one
    or more apk files. These conatiner files contain various apk files, whose
    purpose is noted in the ``manifest.json`` file. This class parses the
    ``manifest.json`` file to determine the base apk file, which is annotated by
    the ``base`` field in the ``split_apks`` object.

    Parameters:
        bytes data: The xapk container file data.
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
    the ``manifest.json`` file. This class parses the ``manifest.json`` file to
    determine the base apk file, which is annotated by the ``base`` field in the
    ``split_apks`` object.

    Parameters:
        str path: The path to the xapk file.
    """

    def __init__(self, path: str):
        super().__init__(path)

    def get_base_apk(self) -> bytes:
        return InMemoryXAPKContainer(pathlib.Path(self.path).read_bytes()).get_base_apk()


class InMemoryAPKSContainer(InMemoryMultiAPKContainer):
    """
    A class that represents an in-memory apks container file which contains one
    or more apk files. This is also known as a split-apk. The base apk in these
    containers is usually named ``base.apk``.

    Parameters:
        bytes data: The apks container file data.
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
    This is also known as a split-apk. The base apk in these containers is
    usually named ``base.apk``.

    Parameters:
        str path: The path to the apks file.
    """

    def __init__(self, path: str):
        super().__init__(path)

    def get_base_apk(self) -> bytes:
        return InMemoryAPKSContainer(pathlib.Path(self.path).read_bytes()).get_base_apk()


class JarContainer(ZipContainer):
    """
    A class that represents a jar file which contains one or more dex files.

    Parameters:
        str path: The path to the jar file.
    """

    def __init__(self, path: str):
        super().__init__(path)


class APKContainer(ZipContainer):
    """
    A class that represents an apk file which contains one or more dex files.
    Only the root files in the archive will be considered.

    Parameters:
        str path: The path to the apk file.
    """

    def __init__(self, path: str):
        super().__init__(path, root_only=True)
