"""Load the native OCR adapter for this Alas checkout and its child processes."""
import importlib.abc
import importlib.util
import os
import sys
from pathlib import Path


class _AlasOcrLoader(importlib.abc.Loader):
    def create_module(self, spec):
        return None

    def exec_module(self, module):
        from alas_onnx_ocr import MacOcr
        module.AlOcr = MacOcr


class _AlasOcrFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname != 'module.ocr.al_ocr' or not path:
            return None
        root = Path(__file__).resolve().parents[2]
        expected = root / 'module' / 'ocr'
        if not any(Path(p).resolve() == expected for p in path):
            return None
        return importlib.util.spec_from_loader(fullname, _AlasOcrLoader())


if sys.platform == 'darwin' and os.environ.get('ALAS_MAC_OCR') == 'onnx':
    sys.path.append(str(Path(__file__).resolve().parent / 'packages'))
    sys.meta_path.insert(0, _AlasOcrFinder())
