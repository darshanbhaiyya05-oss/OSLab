"""In-memory virtual file system: directories, files, metadata."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class VNode:
    name: str
    is_dir: bool
    size: int = 0
    permissions: str = "rw-r--r--"
    children: dict[str, "VNode"] = field(default_factory=dict)
    parent: Optional["VNode"] = field(default=None, repr=False)

    def to_dict(self) -> dict:
        d = {
            "name": self.name,
            "type": "dir" if self.is_dir else "file",
            "permissions": self.permissions,
        }
        if self.is_dir:
            d["children"] = {k: v.to_dict() for k, v in self.children.items()}
        else:
            d["size_bytes"] = self.size
        return d


class VirtualFileSystem:
    def __init__(self) -> None:
        self.root = VNode(name="/", is_dir=True, permissions="rwxr-xr-x")

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _resolve(self, path: str) -> VNode:
        if not path.startswith("/"):
            raise ValueError("Path must start with '/'.")
        parts = [p for p in path.split("/") if p]
        node = self.root
        for part in parts:
            if not node.is_dir:
                raise NotADirectoryError(f"{node.name} is not a directory.")
            if part not in node.children:
                raise FileNotFoundError(f"Path not found: {path}")
            node = node.children[part]
        return node

    def _resolve_parent(self, path: str) -> tuple[VNode, str]:
        if path == "/":
            raise ValueError("Cannot operate on root directly.")
        parts = [p for p in path.split("/") if p]
        name = parts[-1]
        parent_path = "/" + "/".join(parts[:-1])
        parent = self._resolve(parent_path) if parent_path != "/" else self.root
        if not parent.is_dir:
            raise NotADirectoryError(f"{parent.name} is not a directory.")
        return parent, name

    # ------------------------------------------------------------------
    # Operations
    # ------------------------------------------------------------------

    def mkdir(self, path: str, permissions: str = "rwxr-xr-x") -> VNode:
        parent, name = self._resolve_parent(path)
        if name in parent.children:
            raise FileExistsError(f"{name} already exists.")
        node = VNode(name=name, is_dir=True, permissions=permissions, parent=parent)
        parent.children[name] = node
        return node

    def create_file(
        self,
        path: str,
        size: int = 0,
        permissions: str = "rw-r--r--",
    ) -> VNode:
        if size < 0:
            raise ValueError("File size cannot be negative.")
        parent, name = self._resolve_parent(path)
        if name in parent.children:
            raise FileExistsError(f"{name} already exists.")
        node = VNode(
            name=name, is_dir=False, size=size,
            permissions=permissions, parent=parent,
        )
        parent.children[name] = node
        return node

    def delete(self, path: str, recursive: bool = False) -> None:
        parent, name = self._resolve_parent(path)
        if name not in parent.children:
            raise FileNotFoundError(f"{name} not found.")
        node = parent.children[name]
        if node.is_dir and node.children and not recursive:
            raise OSError(f"{name} is a non-empty directory (use recursive=True).")
        del parent.children[name]

    def rename(self, path: str, new_name: str) -> VNode:
        if not new_name or "/" in new_name:
            raise ValueError("Invalid new name.")
        parent, name = self._resolve_parent(path)
        if name not in parent.children:
            raise FileNotFoundError(f"{name} not found.")
        if new_name in parent.children:
            raise FileExistsError(f"{new_name} already exists.")
        node = parent.children.pop(name)
        node.name = new_name
        parent.children[new_name] = node
        return node

    def list_dir(self, path: str = "/") -> list[dict]:
        node = self._resolve(path)
        if not node.is_dir:
            raise NotADirectoryError(f"{path} is not a directory.")
        return [
            {
                "name": child.name,
                "type": "dir" if child.is_dir else "file",
                "size": child.size if not child.is_dir else 0,
                "permissions": child.permissions,
            }
            for child in sorted(node.children.values(), key=lambda c: (not c.is_dir, c.name))
        ]

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return self.root.to_dict()


# ----------------------------------------------------------------------
# Sample tree
# ----------------------------------------------------------------------

def sample_file_system() -> VirtualFileSystem:
    vfs = VirtualFileSystem()
    vfs.mkdir("/home")
    vfs.mkdir("/home/docs")
    vfs.mkdir("/home/programs")
    vfs.create_file("/home/doc1.txt", size=2048)
    vfs.create_file("/home/image.jpg", size=102400)
    vfs.create_file("/home/docs/doc2.txt", size=1024)
    vfs.create_file("/home/programs/app1.exe", size=1048576, permissions="rwxr-xr-x")
    vfs.create_file("/home/programs/app2.exe", size=524288, permissions="rwxr-xr-x")
    return vfs