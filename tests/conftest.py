"""Pytest bootstrap of the test suite.

The screenshot golden test harness lives in module/testing/screenshot.py and is
loaded by module path instead of an installed entry point, so a plain checkout
runs the tests without installing the project. It is registered through
``pytest_plugins`` here rather than through ``-p`` in the ``addopts`` of
pyproject.toml: pytest imports the ``-p`` plugins while preparsing the command
line, which happens before ``pythonpath`` is applied, so ``module`` would not be
importable yet and the run failed with "Error importing plugin".

The repository root reaches sys.path through ``pythonpath = ["."]`` in
pyproject.toml, which also covers the runs started through the pytest console
script instead of ``python -m pytest``.
"""

pytest_plugins = ['module.testing.screenshot']
