"""OSLab — Virtual Operating System Simulator (Streamlit entry point)."""
import streamlit as st

st.set_page_config(
    page_title="OSLab — Virtual OS",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="expanded",
)

DARK_CSS = """
<style>
html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }
.stApp { background-color: #0e1420; color: #e6edf3; }
section[data-testid="stSidebar"] {
    background-color: #0a0f18; border-right: 1px solid #1f2a3a;
}
section[data-testid="stSidebar"] * { color: #cfd8e3; }
h1, h2, h3, h4 { color: #e6edf3; }
.stButton>button {
    background-color: #16203000; border: 1px solid #2a3446; color: #e6edf3;
}
.stButton>button:hover { border-color: #3d8bfd; color: #3d8bfd; }
.stButton>button[kind="primary"] {
    background-color: #3d8bfd; border-color: #3d8bfd; color: #ffffff;
}
.stButton>button[kind="primary"]:hover {
    background-color: #2f6fce; border-color: #2f6fce;
}
div[data-testid="stMetricValue"] { color: #3d8bfd; }
div[data-testid="stMetricLabel"] { color: #7e8ba3; }
.stDataFrame, .stDataFrame * { color: #e6edf3; }
</style>
"""
st.markdown(DARK_CSS, unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown("### Mini OS Simulator")
st.sidebar.caption("Interactive Learning Lab")
st.sidebar.markdown("---")

PAGES = [
    "Dashboard",
    "Process Management",
    "CPU Scheduling",
    "Synchronization",
    "Deadlock Analyzer",
    "Memory Management",
    "Virtual Memory",
    "File & Disk Management",
    "System Software",
    "Reports",
]
page = st.sidebar.radio("Select a module", PAGES, label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.caption("OSLab · ECT7006 · Streamlit build")

# Routing
if page == "Dashboard":
    from modules import dashboard
    dashboard.render(st.session_state)
    
elif page == "Process Management":
    from modules import process_manager
    process_manager.render(st.session_state)

elif page == "CPU Scheduling":
    from modules import cpu_scheduler
    cpu_scheduler.render(st.session_state)

elif page == "Synchronization":
    from modules import synchronization_lab
    synchronization_lab.render(st.session_state)
    
elif page == "Deadlock Analyzer":
    from modules import deadlock_manager
    deadlock_manager.render(st.session_state)
    
elif page == "Memory Management":
    from modules import memory_manager
    memory_manager.render(st.session_state)

elif page == "Virtual Memory":
    from modules import virtual_memory
    virtual_memory.render(st.session_state)

elif page == "File & Disk Management":
    from modules import file_manager, disk_manager
    sub = st.sidebar.radio("Sub-module", ["File Manager", "Disk Scheduling"],
                           label_visibility="collapsed")
    if sub == "File Manager":
        file_manager.render(st.session_state)
    else:
        disk_manager.render(st.session_state)

elif page == "System Software":
    from modules import system_software
    system_software.render(st.session_state)

elif page == "Reports":
    from modules import reports
    reports.render(st.session_state)

else:
    st.markdown(f"## {page}")
    st.info("This module will be delivered in a subsequent build step.")