import typing as t


class TabWrapper:
    def __init__(self, generator, prefix='', suffix=''):
        """
        Args:
            generator (CodeGenerator):
        """
        self.generator = generator
        self.prefix = prefix
        self.suffix = suffix

    def __enter__(self):
        if self.prefix:
            self.generator.add(self.prefix)
        self.generator.tab_count += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.generator.tab_count -= 1
        if self.suffix:
            self.generator.add(self.suffix)


class CodeGenerator:
    def __init__(self):
        self.tab_count = 0
        self.lines = []

    def generate(self) -> t.Iterable[str]:
        yield ''

    def add(self, line, comment=False, newline=True):
        self.lines.append(self._line_with_tabs(line, comment=comment, newline=newline))

    def print(self):
        lines = ''.join(self.lines)
        print(lines)

    def write(self, file: str = None):
        lines = ''.join(self.lines)
        with open(file, 'w', encoding='utf-8', newline='') as f:
            f.write(lines)

    def _line_with_tabs(self, line, comment=False, newline=True):
        if comment:
            line = '# ' + line
        out = '    ' * self.tab_count + line
        if newline:
            out += '\n'
        return out

    def _repr(self, obj):
        if isinstance(obj, str) and '\n' in obj:
            out = '"""\n'
            with self.tab():
                for line in obj.strip().split('\n'):
                    line = line.strip()
                    out += self._line_with_tabs(line)
            out += self._line_with_tabs('"""', newline=False)
            return out
        return repr(obj)

    def tab(self):
        return TabWrapper(self)

    def Value(self, key=None, value=None, **kwargs):
        if key is not None:
            self.add(f'{key} = {self._repr(value)}')
        for key, value in kwargs.items():
            self.Value(key, value)

    def Comment(self, text):
        for line in text.strip().split('\n'):
            line = line.strip()
            self.add(line, comment=True)

    def Dict(self, key):
        return TabWrapper(self, prefix=str(key) + ' = {', suffix='}')

    def DictItem(self, key=None, value=None, **kwargs):
        if key is not None:
            self.add(f'{self._repr(key)}: {self._repr(value)},')
        for key, value in kwargs.items():
            self.DictItem(key, value)


generator = CodeGenerator()
Value = generator.Value
Comment = generator.Comment
Dict = generator.Dict
DictItem = generator.DictItem
