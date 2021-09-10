unary = "abs ceil floor invert neg pos round trunc".split()
binary = "add sub mul floordiv div truediv mod divmod pow lshift rshift and or xor".split()
binary = binary + [f"r{name}" for name in binary] + [f"i{name}" for name in binary]
compare = "cmp eq ne lt gt le ge".split()
serial = "len getitem setitem delitem iter reversed contains missing".split()
dunders = tuple(f"__{name}__" for name in unary + binary + compare + serial)


def mathdunders(cls):
    """
    https://github.com/discretegames/mathdunders/blob/main/mathdunders/mathdunders.py

    Args:
        cls:

    Returns:

    """
    def make_dunder(attr):
        def dunder(self, *args):
            return self.value.__getattribute__(attr)(*args)

        return dunder

    for name in dunders:
        setattr(cls, name, make_dunder(name))
    return cls


@mathdunders
class Argument:
    path = ''
    path_arg = ''
    path_func = ''
    option = ()

    has_option = False
    has_bind = False

    def __init__(self, path, value, option=()):
        self.path_arg = path
        self.value = value
        self.option = option
        self.has_option = bool(option)

    def set(self, value):
        self.value = value

    def bind(self, func, value):
        self.path_func = func
        self.path = f'{self.path_func}.{self.path_arg}'
        self.value = value
        self.has_bind = True

    def __repr__(self):
        return f'Argument(value={repr(self.value)}, path={repr(self.path)})'

    def __str__(self):
        return str(self.value)

    def __bool__(self):
        return bool(self.value)

    def __hash__(self):
        return hash(self.path)
