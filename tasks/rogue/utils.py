import re

REGEX_PUNCTUATION = re.compile(r'[ ,.\'"“”，。:：!！?？·•—/()（）「」『』【】《》]')


def parse_name(n):
    n = REGEX_PUNCTUATION.sub('', str(n)).lower()
    return n


def get_regex_from_keyword_name(keyword, attr_name):
    string = ""
    for instance in keyword.instances.values():
        if hasattr(instance, attr_name):
            for name in instance.__getattribute__(attr_name):
                string += f"{name}|"
    # some pattern contain each other, make sure each pattern end with "-" or the end of string
    return f"(?:({string[:-1]})(?:-|$))?"
