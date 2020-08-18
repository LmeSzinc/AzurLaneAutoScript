import re

from module.logger import logger


class Filter:
    def __init__(self, regex, attr, preset):
        """
        Args:
            regex: Regular expression.
            attr: Attribute name.
            preset: Build-in string preset.
        """
        self.regex = regex
        self.attr = attr
        self.preset = preset
        self.filter_raw = []
        self.filter = []

    def load(self, string):
        self.filter_raw = [f.strip() for f in string.split('>')]
        self.filter = [self.parse_filter(f) for f in self.filter_raw]

    def is_preset(self, filter):
        return filter in self.preset

    def apply(self, objs):
        """
        Args:
            objs (list[object]):

        Returns:
            list: A list of str and int, such as [2, 3, 0, 'reset']
        """
        out = []
        for raw, filter in zip(self.filter_raw, self.filter):
            if self.is_preset(raw):
                out.append(raw)
            else:
                for index, obj in enumerate(objs):
                    if self.apply_filter_to_obj(obj=obj, filter=filter) and index not in out:
                        out.append(index)

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
            if obj.__getattribute__(attr).lower() != value:
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
            logger.warning(f'Invalid filter: {string}')
            # Invalid filter will be ignored.
            # Return strange things and make it impossible to match
            return ['1nVa1d'] + [None] * (len(self.attr) - 1)
