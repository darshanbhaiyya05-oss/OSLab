"""Module 7 — System Software Laboratory."""
from __future__ import annotations
import streamlit as st


PIPELINE_STAGES = [
    ("Source code",
     "Human-readable program written in a high-level language (e.g. C, Python)."),
    ("Preprocessor",
     "Handles #include, #define, and macro expansion. Produces expanded source."),
    ("Compiler",
     "Translates preprocessed source into assembly code for the target CPU."),
    ("Assembler",
     "Converts assembly into machine-code object files (.o / .obj)."),
    ("Linker",
     "Combines object files and libraries into a single executable."),
    ("Loader",
     "Places the executable into memory and hands control to its entry point."),
    ("Runtime + Debugger",
     "Runs the program; a debugger can attach to inspect state."),
]


OS_SERVICES = [
    ("Process management",   "create, terminate, schedule, synchronize"),
    ("Memory management",    "allocate, free, page, swap"),
    ("File management",      "create, read, write, delete, list"),
    ("I/O management",       "device drivers, buffering, spooling"),
    ("Protection & security","permissions, access control, isolation"),
    ("Error detection",      "traps, interrupts, exception handling"),
    ("Accounting",           "resource usage, logging, quotas"),
]


SYSCALL_EXAMPLES = [
    ("Process",  "fork() / exec() / wait() / exit()",
     "Create, replace, wait for, or end a process."),
    ("File",     "open() / read() / write() / close()",
     "Operate on a file descriptor returned by open()."),
    ("Memory",   "brk() / mmap() / munmap()",
     "Grow the heap or map files into the address space."),
    ("Device",   "ioctl() / read() / write()",
     "Communicate with a device driver."),
    ("Info",     "getpid() / gettimeofday() / stat()",
     "Retrieve process, time, or file-system information."),
]


def render(session_state) -> None:
    st.markdown("## System Software Laboratory")
    st.caption("Compilation pipeline, OS services, and system-call concepts.")

    tab1, tab2, tab3 = st.tabs(["Compilation Pipeline", "OS Services", "System Calls"])

    # ------------------------------------------------------------------
    # Compilation pipeline
    # ------------------------------------------------------------------
    with tab1:
        st.markdown("### From Source to Executable")
        for i, (stage, desc) in enumerate(PIPELINE_STAGES):
            with st.container(border=True):
                c1, c2 = st.columns([1, 3])
                c1.markdown(f"**{i+1}. {stage}**")
                c2.write(desc)

        st.markdown("### Example")
        st.code(
            "// hello.c\n"
            "#include <stdio.h>\n"
            "int main(void) {\n"
            "    printf(\"Hello, OSLab!\\n\");\n"
            "    return 0;\n"
            "}",
            language="c",
        )
        st.caption("Command-line toolchain that would process this file:")
        st.code(
            "gcc -E  hello.c  -o hello.i    # preprocess\n"
            "gcc -S  hello.i  -o hello.s    # compile to assembly\n"
            "gcc -c  hello.s  -o hello.o    # assemble to object\n"
            "gcc     hello.o  -o hello      # link\n"
            "./hello                        # load & run",
            language="bash",
        )
        st.info(
            "OSLab does not implement a real compiler. The pipeline above is "
            "the conceptual model that the loader and OS services cooperate with."
        )

    # ------------------------------------------------------------------
    # OS services
    # ------------------------------------------------------------------
    with tab2:
        st.markdown("### Operating-System Services")
        for name, desc in OS_SERVICES:
            with st.container(border=True):
                c1, c2 = st.columns([1, 3])
                c1.markdown(f"**{name}**")
                c2.write(desc)

        st.markdown("### Where OSLab touches each service")
        st.markdown(
            "- **Process management** — CPU Scheduler, Process state transitions.\n"
            "- **Memory management** — Memory Management, Virtual Memory modules.\n"
            "- **File management** — Virtual File Manager.\n"
            "- **I/O management** — Disk Scheduling.\n"
            "- **Protection** — File permissions in the VFS.\n"
            "- **Error detection** — Input validation on every form.\n"
            "- **Accounting** — Event log timestamps."
        )

    # ------------------------------------------------------------------
    # System calls
    # ------------------------------------------------------------------
    with tab3:
        st.markdown("### System-Call Categories")
        for cat, calls, desc in SYSCALL_EXAMPLES:
            with st.container(border=True):
                c1, c2 = st.columns([1, 3])
                c1.markdown(f"**{cat}**")
                c2.markdown(f"`{calls}` — {desc}")

        st.markdown("### Conceptual example")
        st.code(
            "// User program calls printf()\n"
            "printf(\"Hello\\n\");\n"
            "\n"
            "// libc converts it into write()\n"
            "write(STDOUT_FILENO, buf, len);\n"
            "\n"
            "// Kernel services the write syscall\n"
            "//   -> copies user buffer into kernel space\n"
            "//   -> dispatches to the terminal driver\n"
            "//   -> returns the byte count to the user program",
            language="c",
        )
        st.warning(
            "OSLab is a user-space simulator. Python's open() is a library call "
            "serviced by the host operating system — it is not an OSLab syscall. "
            "This page explains the concept, not an implementation."
        )