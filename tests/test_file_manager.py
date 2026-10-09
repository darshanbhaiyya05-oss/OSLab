"""Tests for the virtual file system."""
import pytest
from algorithms.file_system import VirtualFileSystem, sample_file_system


def test_create_file_and_mkdir():
    vfs = VirtualFileSystem()
    vfs.mkdir("/home")
    vfs.create_file("/home/a.txt", size=100)
    entries = {e["name"]: e for e in vfs.list_dir("/home")}
    assert "a.txt" in entries
    assert entries["a.txt"]["size"] == 100


def test_create_rejects_duplicate():
    vfs = VirtualFileSystem()
    vfs.mkdir("/home")
    vfs.create_file("/home/a.txt")
    with pytest.raises(FileExistsError):
        vfs.create_file("/home/a.txt")


def test_delete_empty_file():
    vfs = VirtualFileSystem()
    vfs.mkdir("/home")
    vfs.create_file("/home/a.txt")
    vfs.delete("/home/a.txt")
    assert vfs.list_dir("/home") == []


def test_delete_nonempty_dir_requires_recursive():
    vfs = VirtualFileSystem()
    vfs.mkdir("/home")
    vfs.create_file("/home/a.txt")
    with pytest.raises(OSError):
        vfs.delete("/home")
    vfs.delete("/home", recursive=True)
    assert vfs.list_dir("/") == []


def test_rename():
    vfs = VirtualFileSystem()
    vfs.mkdir("/home")
    vfs.create_file("/home/a.txt", size=10)
    vfs.rename("/home/a.txt", "b.txt")
    entries = {e["name"] for e in vfs.list_dir("/home")}
    assert entries == {"b.txt"}


def test_rename_rejects_existing_name():
    vfs = VirtualFileSystem()
    vfs.mkdir("/home")
    vfs.create_file("/home/a.txt")
    vfs.create_file("/home/b.txt")
    with pytest.raises(FileExistsError):
        vfs.rename("/home/a.txt", "b.txt")


def test_missing_path_raises():
    vfs = VirtualFileSystem()
    with pytest.raises(FileNotFoundError):
        vfs.list_dir("/nope")


def test_sample_file_system_structure():
    vfs = sample_file_system()
    home = {e["name"]: e for e in vfs.list_dir("/home")}
    assert "docs" in home and home["docs"]["type"] == "dir"
    assert "programs" in home
    assert "doc1.txt" in home
    docs = {e["name"]: e for e in vfs.list_dir("/home/docs")}
    assert "doc2.txt" in docs


def test_negative_file_size_rejected():
    vfs = VirtualFileSystem()
    vfs.mkdir("/home")
    with pytest.raises(ValueError):
        vfs.create_file("/home/a.txt", size=-5)