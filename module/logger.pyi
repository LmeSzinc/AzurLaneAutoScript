from collections.abc import Callable

from loguru import Logger
from rich.console import ConsoleRenderable
from rich.highlighter import RegexHighlighter
from rich.theme import Theme

class Highlighter(RegexHighlighter): ...

WEB_THEME: Theme

logger_debug: bool
pyw_name: str

def set_file_logger(
    name: str = pyw_name,
) -> None: ...
def set_func_logger(
    func: Callable[[ConsoleRenderable], None],
) -> None: ...
def rule(
    title: str = "",
    *,
    characters: str = "─",
    style: str = "rule.line",
    end: str = "\n",
    align: str = "center",
) -> None: ...
def hr(
    title,
    level: int = 3,
) -> None: ...
def attr(
    name,
    text,
) -> None: ...
def attr_align(
    name,
    text,
    front: str = "",
    align: int = 22,
) -> None: ...
def cleanup_old_logs(
    directory: str = "./log",
    days: int = 30,
) -> None: ...

class __logger(Logger):
    log_file: str
    def rule(
        self,
        title: str = "",
        *,
        characters: str = "─",
        style: str = "rule.line",
        end: str = "\n",
        align: str = "center",
    ) -> None: ...
    def hr(
        self,
        title,
        level: int = 3,
    ) -> None: ...
    def attr(
        self,
        name,
        text,
    ) -> None: ...
    def attr_align(
        self,
        name,
        text,
        front: str = "",
        align: int = 22,
    ) -> None: ...
    def set_file_logger(
        self,
        name: str = pyw_name,
    ) -> None: ...
    def set_func_logger(
        self,
        func: Callable[[ConsoleRenderable], None],
    ) -> None: ...

logger: __logger
