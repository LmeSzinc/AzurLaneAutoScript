# -*- mode: python ; coding: utf-8 -*-
"""
DRAFT PyInstaller spec for the Alas backend sidecar (onedir).

Validate on a packaging machine before shipping: the datas list must match
the real runtime needs (see deploy/packaging/README.md). Build with:

    pyinstaller --clean --noconfirm deploy/packaging/alas_backend.spec

Result: dist/alas-backend/ with alas-backend.exe as the entry point.
"""

import os

from PyInstaller.config import CONF
from PyInstaller.utils.hooks import collect_all

# Repo root: spec lives in <root>/deploy/packaging/
root = os.path.abspath(os.path.join(SPECPATH, "..", ".."))

# Anchor the output locations to the repo root. PyInstaller otherwise
# defaults distpath/workpath to the *current working directory*, so running
# the spec from webapp-tauri/ (pnpm build:sidecar) or the repo root (CI)
# would place artifacts in different spots and tauri-build's resource check
# for ../../dist/alas-backend (relative to src-tauri/) would fail again.
CONF["distpath"] = os.path.join(root, "dist")
CONF["workpath"] = os.path.join(root, "build", "alas_backend")

datas = [
    # Runtime directories the backend opens with relative paths (./config, ./assets, ./bin).
    # Absolute paths: PyInstaller resolves relative entries against SPECPATH.
    (os.path.join(root, "assets"), "assets"),
    (os.path.join(root, "bin"), "bin"),
    (os.path.join(root, "config"), "config"),
    # In-tree schemas/i18n read via module-relative paths.
    (os.path.join(root, "module/config"), "module/config"),
    (os.path.join(root, "module/submodule"), "module/submodule"),
    # Production SPA build served by module/webui/api (StaticFiles at "/").
    # Built with `pnpm build` in webapp-tauri/; keep the tree layout because
    # the backend resolves webapp-tauri/dist relative to the repo root.
    (os.path.join(root, "webapp-tauri/dist"), "webapp-tauri/dist"),
]

binaries = []
data = []
hiddenimports = [
    "uvicorn.logging",
    "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan.on",
    "websockets.legacy",
    "multipart",
]
for pkg in ("cv2", "onnxruntime", "scipy", "av", "PIL"):
    b, d, h = collect_all(pkg)
    binaries += b
    data += d
    hiddenimports += h

a = Analysis(
    [os.path.join(root, "gui.py")],
    # Project modules (root) plus the synced venv site-packages (CI runs
    # `uv sync` first, so .venv/Lib/site-packages holds the locked deps).
    # pathex only feeds the ANALYSIS search path; the pyinstaller process
    # itself keeps its own environment, so packaging-20.9 (pinned by
    # uiautomator2 for Python>=3.12) never shadows the builder's runtime.
    pathex=[root, os.path.join(root, ".venv", "Lib", "site-packages")],
    binaries=binaries,
    datas=datas + data,
    hiddenimports=hiddenimports,
    excludes=["tkinter", "matplotlib", "pandas", "PyQt5", "PySide6"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="alas-backend",
    # console=True on purpose: windowed PyInstaller apps route uncaught
    # tracebacks to a modal dialog (which hangs the app invisibly); with a
    # console subsystem the traceback goes to stderr, which the shell
    # mirrors to <app_log_dir>/backend.log. The shell spawns the sidecar
    # with CREATE_NO_WINDOW, so users never see the console.
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="alas-backend",
)
