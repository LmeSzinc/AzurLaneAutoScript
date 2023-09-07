import re

from module.logger import logger


class Filter:
    def __init__(self, regex, attr, preset=()):
        """
        Args:
            regex: Regular expression.
            attr: Attribute name.
            preset: Build-in string preset.
        """
        if isinstance(regex, str):
            regex = re.compile(regex)
        self.regex = regex
        self.attr = attr
        self.preset = tuple(list(p.lower() for p in preset))
        self.filter_raw = []
        self.filter = []

    def load(self, string):
        """
        Load a filter string, filters are connected with ">"

        There are also tons of unicode characters similar to ">"
        > \u003E correct
        ＞ \uFF1E
        ﹥ \uFE65
        › \u203a
        ˃ \u02c3
        ᐳ \u1433
        ❯ \u276F
        """
        string = str(string)
        string = re.sub(r'[ \t\r\n]', '', string)
        string = re.sub(r'[＞﹥›˃ᐳ❯]', '>', string)
        self.filter_raw = string.split('>')
        self.filter = [self.parse_filter(f) for f in self.filter_raw]

    def is_preset(self, filter):
        return len(filter) and filter.lower() in self.preset

    def apply(self, objs, func=None):
        """
        Args:
            objs (list): List of objects and strings
            func (callable): A function to filter object.
                Function should receive an object as arguments, and return a bool.
                True means add it to output.

        Returns:
            list: A list of objects and preset strings, such as [object, object, object, 'reset']
        """
        out = []
        for raw, filter in zip(self.filter_raw, self.filter):
            if self.is_preset(raw):
                raw = raw.lower()
                if raw not in out:
                    out.append(raw)
            else:
                for index, obj in enumerate(objs):
                    if self.apply_filter_to_obj(obj=obj, filter=filter) and obj not in out:
                        out.append(obj)

        if func is not None:
            objs, out = out, []
            for obj in objs:
                if isinstance(obj, str):
                    out.append(obj)
                elif func(obj):
                    out.append(obj)
                else:
                    # Drop this object
                    pass

        return out

    def apply_filter_to_obj(self, obj, filter):
        """
        Args:
            obj (object):
            filter (list[str]):

        Returns:
            bool: If an object satisfy a filter.
        """

        for attr, value in zip(self.attr, filter):
            if not value:
                continue
            if str(obj.__getattribute__(attr)).lower() != str(value):
                return False

        return True

    def parse_filter(self, string):
        """
        Args:
            string (str):

        Returns:
            list[strNone]:
        """
        string = string.replace(' ', '').lower()
        result = re.search(self.regex, string)

        if self.is_preset(string):
            return [string]

        if result and len(string) and result.span()[1]:
            return [result.group(index + 1) for index, attr in enumerate(self.attr)]
        else:
            logger.warning(f'Invalid filter: "{string}". This selector does not match the regex, nor a preset.')
            # Invalid filter will be ignored.
            # Return strange things and make it impossible to match
            return ['1nVa1d'] + [None] * (len(self.attr) - 1)
