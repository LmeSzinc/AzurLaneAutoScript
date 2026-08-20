import os
import sys


def get_resource_root():
    """Root of the read-only bundled resources.

    Frozen (PyInstaller onedir sidecar): the directory containing the
    executable - the bundle carries module/config, module/submodule and
    webapp-tauri/dist relative to it.
    Source checkout: the repository root.

    The process CWD is the writable user data directory (the repo in a
    source run, ALAS_DATA_DIR in an installed run), so legacy CWD-relative
    paths that point at bundled content must resolve from here instead.
    """
    if getattr(sys, "frozen", False):
        # PyInstaller onedir bundles datas under the _internal directory
        # (sys._MEIPASS points there), not next to the executable.
        return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(sys.executable)))
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))
