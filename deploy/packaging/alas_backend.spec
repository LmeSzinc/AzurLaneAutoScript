# -*- mode: python ; coding: utf-8 -*-
"""
DRAFT PyInstaller spec for the Alas backend sidecar (onedir).

Validate on a packaging machine before shipping: the datas list must match
the real runtime needs (see deploy/packaging/README.md). Build with:

    pyinstaller --clean --noconfirm deploy/packaging/alas_backend.spec

Result: dist/alas-backend/ with alas-backend.exe as the entry point.
"""

import os

from PyInstaller.utils.hooks import collect_all

# Repo root: spec lives in <root>/deploy/packaging/
root = os.path.abspath(os.path.join(SPECPATH, "..", ".."))

datas = [
    # Runtime directories the backend opens with relative paths (./config, ./assets, ./bin).
    ("assets", "assets"),
    ("bin", "bin"),
    ("config", "config"),
    # In-tree schemas/i18n read via module-relative paths.
    ("module/config", "module/config"),
    ("module/submodule", "module/submodule"),
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
    pathex=[root],
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
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="alas-backend",
)
