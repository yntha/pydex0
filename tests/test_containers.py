import pytest
import os

from datastream import ByteOrder
from pydex.containers import ZipContainer, JarContainer, XAPKContainer, APKSContainer, APKContainer


def get_test_container(name: str) -> str:
    root_dir = os.getcwd()

    return os.path.join(root_dir, "resources", "containers", name)


def test_apk_container():
    container = APKContainer(get_test_container("sample.apk"))
    container_dex_files = container.fetch_dex_files()

    assert len(container_dex_files.dex_files) == 1


def test_jar_container():
    container = JarContainer(get_test_container("sample.jar"))
    container_dex_files = container.fetch_dex_files()

    assert len(container_dex_files.dex_files) == 1


def test_xapk_container():
    container = XAPKContainer(get_test_container("sample.xapk"))
    container_dex_files = container.fetch_dex_files()

    assert len(container_dex_files.dex_files) == 1


def test_apks_container():
    container = APKSContainer(get_test_container("sample.apks"))
    container_dex_files = container.fetch_dex_files()

    assert len(container_dex_files.dex_files) == 1


def test_zip_container():
    container = ZipContainer(get_test_container("sample.zip"))
    container_dex_files = container.fetch_dex_files()

    assert len(container_dex_files.dex_files) == 1
