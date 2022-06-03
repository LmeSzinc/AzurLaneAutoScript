import os
import re

DEPLOY_CONFIG = "./config/deploy.yaml"
DEPLOY_TEMPLATE = "./deploy/template"


class cached_property:
    """
    cached-property from https://github.com/pydanny/cached-property

    A property that is only computed once per instance and then replaces itself
    with an ordinary attribute. Deleting the attribute resets the property.
    Source: https://github.com/bottlepy/bottle/commit/fa7733e075da0d790d809aa3d2f53071897e6f76
    """

    def __init__(self, func):
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self

        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


def poor_yaml_read(file):
    """
    Poor implementation to load yaml without pyyaml dependency, but with re

    Args:
        file (str):

    Returns:
        dict:
    """
    if not os.path.exists(file):
        return {}

    data = {}
    regex = re.compile(r"^(.*?):(.*?)$")
    with open(file, "r", encoding="utf-8") as f:
        for line in f.readlines():
            line = line.strip("\n\r\t ").replace("\\", "/")
            if line.startswith("#"):
                continue
            result = re.match(regex, line)
            if result:
                k, v = result.group(1), result.group(2).strip("\n\r\t' ")
                if v:
                    if v == "null":
                        v = ""
                    data[k] = v

    return data


def poor_yaml_write(data, file, template_file=DEPLOY_TEMPLATE):
    """
    Args:
        data (dict):
        file (str):
        template_file (str):
    """
    with open(template_file, "r", encoding="utf-8") as f:
        text = f.read().replace("\\", "/")

    for key, value in data.items():
        if value is "":
            value = "null"
        text = re.sub(f"{key}:.*?\n", f"{key}: {value}\n", text)

    with open(file, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def hr1(title):
    print("=" * 20 + " " + title + " " + "=" * 20)


def hr0(title):
    middle = "|" + " " * 20 + title + " " * 20 + "|"
    border = "+" + "-" * (len(middle) - 2) + "+"
    print(border)
    print(middle)
    print(border)
