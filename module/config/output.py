"""
Minimal stand-in for pywebio.io_ctrl.Output.

The legacy pywebio GUI used Output objects to define form widgets; the
Svelte frontend renders forms from the args schema instead. This class
only keeps the config system's type hierarchy intact.
"""


class Output:
    def __init__(self, spec, on_embed=None):
        self.spec = spec

    def show(self):
        pass
