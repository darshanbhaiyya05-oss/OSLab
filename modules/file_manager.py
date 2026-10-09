"""Module 6a — Virtual File Manager."""
from __future__ import annotations
import json
import pandas as pd
import streamlit as st
from algorithms.file_system import VirtualFileSystem, sample_file_system


def _init_fs(session_state) -> None:
    if "vfs" not in session_state:
        session_state["vfs"] = sample_file_system()


def _render_tree(node: dict, prefix: str = "", is_last: bool = True) -> str:
    """Return ASCII tree of the file system."""
    lines = []
    icon = "📁" if node["type"] == "dir" else "📄"

    if prefix == "":
        lines.append(f"{icon} {node['name']}")
    else:
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{icon} {node['name']}")

    if node["type"] == "dir":
        children = list(node.get("children", {}).values())
        for i, child in enumerate(children):
            child_is_last = (i == len(children) - 1)
            extension = "    " if is_last else "│   "
            lines.append(_render_tree(child, prefix + extension, child_is_last))
    return "\n".join(lines)


def render(session_state) -> None:
    st.markdown("## Virtual File Manager")
    st.caption("In-memory directory tree — does not touch your real file system.")
    _init_fs(session_state)
    vfs: VirtualFileSystem = session_state["vfs"]

    tab1, tab2, tab3 = st.tabs(["Browse", "Operations", "Raw JSON"])

    with tab1:
        st.markdown("### Directory Tree")
        st.code(_render_tree(vfs.to_dict()), language="text")

        path = st.text_input("List directory", value="/home", key="ls_path")
        if st.button("List", key="ls_btn"):
            try:
                entries = vfs.list_dir(path)
                st.dataframe(pd.DataFrame(entries),
                             use_container_width=True, hide_index=True)
            except (FileNotFoundError, NotADirectoryError) as exc:
                st.error(str(exc))

    with tab2:
        st.markdown("### Create / Rename / Delete")

        op = st.radio("Operation", ["Create file", "Create dir", "Rename", "Delete"],
                      horizontal=True, key="fs_op")

        with st.form("fs_form", clear_on_submit=False):
            if op == "Create file":
                path = st.text_input("Full path", value="/home/new.txt")
                size = st.number_input("Size (bytes)", min_value=0, value=512, step=128)
                perms = st.text_input("Permissions", value="rw-r--r--")
                submitted = st.form_submit_button("Create file")
                if submitted:
                    try:
                        vfs.create_file(path, size=int(size), permissions=perms)
                        st.success(f"Created file {path}.")
                    except (FileExistsError, FileNotFoundError,
                            NotADirectoryError, ValueError) as exc:
                        st.error(str(exc))

            elif op == "Create dir":
                path = st.text_input("Full path", value="/home/newdir")
                submitted = st.form_submit_button("Create directory")
                if submitted:
                    try:
                        vfs.mkdir(path)
                        st.success(f"Created directory {path}.")
                    except (FileExistsError, FileNotFoundError,
                            NotADirectoryError, ValueError) as exc:
                        st.error(str(exc))

            elif op == "Rename":
                path = st.text_input("Existing path", value="/home/doc1.txt")
                new_name = st.text_input("New name", value="renamed.txt")
                submitted = st.form_submit_button("Rename")
                if submitted:
                    try:
                        vfs.rename(path, new_name)
                        st.success(f"Renamed {path} → {new_name}.")
                    except (FileNotFoundError, FileExistsError, ValueError) as exc:
                        st.error(str(exc))

            else:  # Delete
                path = st.text_input("Path to delete", value="/home/doc1.txt")
                recursive = st.checkbox("Recursive (needed for non-empty directories)")
                submitted = st.form_submit_button("Delete")
                if submitted:
                    try:
                        vfs.delete(path, recursive=recursive)
                        st.success(f"Deleted {path}.")
                    except (FileNotFoundError, OSError) as exc:
                        st.error(str(exc))

        if st.button("Reset to sample tree", key="fs_reset"):
            session_state["vfs"] = sample_file_system()
            st.rerun()

    with tab3:
        st.markdown("### Serialized Tree")
        st.json(vfs.to_dict(), expanded=False)
        st.download_button(
            "⬇ Download File System JSON",
            data=json.dumps(vfs.to_dict(), indent=2),
            file_name="vfs_snapshot.json",
            mime="application/json",
        )