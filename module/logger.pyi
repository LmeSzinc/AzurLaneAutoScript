import logging
from typing import Any, Callable

from rich.highlighter import RegexHighlighter
from rich.console import Console, ConsoleRenderable
from rich.theme import Theme

class HTMLConsole(Console): ...
class Highlighter(RegexHighlighter): ...

WEB_THEME: Theme

logger_debug: bool
pyw_name: str

file_formatter: logging.Formatter
console_formatter: logging.Formatter
web_formatter: logging.Formatter

stdout_console: Console

class __logger(logging.Logger):
    def rule(
        title: str = "",
        *,
        characters: str = "-",
        style: str = "rule.line",
        end: str = "\n",
        align: str = "center",
    ) -> None: ...
    def hr(
        title: str,
        level: int = 3,
    ) -> None: ...
    def attr(
        name: str,
        text: str,
    ) -> None: ...
    def attr_align(
        name: str,
        text: str,
        front: str = "",
        align: int = 22,
    ) -> None: ...
    def set_file_logger(
        name: str = pyw_name,
    ) -> None: ...
    def set_func_logger(
        func: Callable[[Any], Any],
    ) -> None: ...
    def print(
        *objects: ConsoleRenderable,
        **kwargs,
    ) -> None: ...

logger: __logger
