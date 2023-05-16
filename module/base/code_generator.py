import typing as t


class TabWrapper:
    def __init__(self, generator, prefix='', suffix='', newline=True):
        """
        Args:
            generator (CodeGenerator):
        """
        self.generator = generator
        self.prefix = prefix
        self.suffix = suffix
        self.newline = newline

        self.nested = False

    def __enter__(self):
        if not self.nested and self.prefix:
            self.generator.add(self.prefix, newline=self.newline)
        self.generator.tab_count += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.generator.tab_count -= 1
        if self.suffix:
            self.generator.add(self.suffix)

    def __repr__(self):
        return self.prefix

    def set_nested(self, suffix=''):
        self.nested = True
        self.suffix += suffix


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
        if isinstance(obj, str):
            if '\n' in obj:
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

    def Empty(self):
        self.add('')

    def Import(self, text, empty=2):
        for line in text.strip().split('\n'):
            line = line.strip()
            self.add(line)
        for _ in range(empty):
            self.Empty()

    def Value(self, key=None, value=None, type_=None, **kwargs):
        if key is not None:
            if type_ is not None:
                self.add(f'{key}: {type_} = {self._repr(value)}')
            else:
                self.add(f'{key} = {self._repr(value)}')
        for key, value in kwargs.items():
            self.Value(key, value)

    def Comment(self, text):
        for line in text.strip().split('\n'):
            line = line.strip()
            self.add(line, comment=True)

    def List(self, key=None):
        if key is not None:
            return TabWrapper(self, prefix=str(key) + ' = [', suffix=']')
        else:
            return TabWrapper(self, prefix='[', suffix=']', newline=False)

    def ListItem(self, value):
        if isinstance(value, TabWrapper):
            value.set_nested(suffix=',')
            self.add(f'{self._repr(value)}')
            return value
        else:
            self.add(f'{self._repr(value)},')

    def Dict(self, key=None):
        if key is not None:
            return TabWrapper(self, prefix=str(key) + ' = {', suffix='}')
        else:
            return TabWrapper(self, prefix='{', suffix='}', newline=False)

    def DictItem(self, key=None, value=None):
        if isinstance(value, TabWrapper):
            value.set_nested(suffix=',')
            if key is not None:
                self.add(f'{self._repr(key)}: {self._repr(value)}')
            return value
        else:
            if key is not None:
                self.add(f'{self._repr(key)}: {self._repr(value)},')

    def Object(self, object_class, key=None):
        if key is not None:
            return TabWrapper(self, prefix=f'{key} = {object_class}(', suffix=')')
        else:
            return TabWrapper(self, prefix=f'{object_class}(', suffix=')', newline=False)

    def ObjectAttr(self, key=None, value=None):
        if isinstance(value, TabWrapper):
            value.set_nested(suffix=',')
            if key is None:
                self.add(f'{self._repr(value)}')
            else:
                self.add(f'{key}={self._repr(value)}')
            return value
        else:
            if key is None:
                self.add(f'{self._repr(value)},')
            else:
                self.add(f'{key}={self._repr(value)},')

    def Class(self, name, inherit=None):
        if inherit is not None:
            return TabWrapper(self, prefix=f'class {name}({inherit}):')
        else:
            return TabWrapper(self, prefix=f'class {name}:')

    def Def(self, name, args=''):
        return TabWrapper(self, prefix=f'def {name}({args}):')


generator = CodeGenerator()
Import = generator.Import
Value = generator.Value
Comment = generator.Comment
Dict = generator.Dict
DictItem = generator.DictItem
