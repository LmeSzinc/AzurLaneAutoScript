"""Logging stack backed by loguru (L1 rewrite).

The public surface is unchanged from the previous rich-logging
implementation, so the 200+ `from module.logger import logger` sites keep
working untouched:

    from module.logger import logger, set_file_logger, set_func_logger
    logger.info / warning / error / critical / debug / exception(...)
    logger.hr(title, level) / attr / attr_align / rule
    logger.log_file  (path of the active file sink)

Three sinks:

- stdout: a rich-based sink that mirrors the pre-loguru RichHandler look
  (padded `logging.level.*` level column, `YYYY-MM-DD HH:mm:ss.mmm │ ` time,
  ReprHighlighter syntax highlighting, rich tracebacks, styled hr rules).
  Rendered by a plain `rich.console.Console` (default theme), like before.
- file: `./log/{date}_{name}.txt` with size rotation and gz compression;
  `set_file_logger(name)` switches the active file, keeping the legacy
  date-per-name convention, and `logger.log_file` tracks it so
  alas.save_error_log() still packages the right file (the `═` separator
  lines emitted by `hr(level=0/1)` are preserved for its split regex).
- func stream: `set_func_logger(func)` delivers rich ConsoleRenderables
  (level column + `HH:MM:SS.mmm │ ` time + message + rich traceback,
  highlighted with the legacy Highlighter/WEB_THEME) into a callable. The
  webui child puts them into a multiprocessing queue and the parent renders
  them unchanged (process_manager.renderables / helpers.render_log), so the
  streaming contract is untouched.

Semantic notes:

- `error(Exception)` converts to "<Type>: <message>" and
  `exception(e)` logs with the traceback (diagnose=True adds local
  variables to the file sink, rich tracebacks to stdout/webui), matching
  the legacy handlers.
- `hr`/`rule` emit plain text (files and the `═` split regex stay intact)
  and flag the record with an `alas_style` extra; the rich sinks restyle
  that text as the old rich `Rule` / `[bold]` markup did:
  `banner` -> bold, `rule_line` -> `rule.line` color, `rule_title` ->
  `rule.text` (bold in WEB_THEME, plain on the default console theme).
- %-style lazy formatting is not supported (loguru uses {}); the 43
  legacy call sites were migrated in L2.
"""

import contextlib
import datetime

# packaging==20.9 (pinned by the uiautomator2==2.16.17 metadata) imports
# stdlib distutils, which no longer exists on Python 3.12+. Importing
# distutils once here, at the root of every ALAS import chain (webui
# process, task subprocesses, desktop backend), pins the setuptools shim
# into sys.modules before anything reaches packaging.utils and avoids
# "ModuleNotFoundError: No module named 'distutils'".
with contextlib.suppress(ImportError):  # pragma: no cover - setuptools is always installed
    import distutils  # noqa: F401

import os
import sys
import time
import typing as t

from loguru import logger as _logger
from rich._log_render import LogRender
from rich.console import Console
from rich.highlighter import RegexHighlighter, ReprHighlighter
from rich.style import Style
from rich.text import Text
from rich.theme import Theme
from rich.traceback import Traceback


class Highlighter(RegexHighlighter):
    base_style = "web."
    highlights = [
        # (r'(?P<datetime>(\d{2}|\d{4})(?:\-)?([0]{1}\d{1}|[1]{1}[0-2]{1})'
        #  r'(?:\-)?([0-2]{1}\d{1}|[3]{1}[0-1]{1})(?:\s)?([0-1]{1}\d{1}|'
        #  r'[2]{1}[0-3]{1})(?::)?([0-5]{1}\d{1})(?::)?([0-5]{1}\d{1}).\d+\b)'),
        (
            r"(?P<time>([0-1]{1}\d{1}|[2]{1}[0-3]{1})(?::)?"
            r"([0-5]{1}\d{1})(?::)?([0-5]{1}\d{1})(.\d+\b))"
        ),
        r"(?P<brace>[\{\[\(\)\]\}])",
        r"\b(?P<bool_true>True)\b|\b(?P<bool_false>False)\b|\b(?P<none>None)\b",
        r"(?P<path>(([A-Za-z]\:)|.)?\B([\/\\][\w\.\-\_\+]+)*[\/\\])(?P<filename>[\w\.\-\_\+]*)?",
        # r"(?<![\\\w])(?P<str>b?\'\'\'.*?(?<!\\)\'\'\'|b?\'.*?(?<!\\)\'|b?\"\"\".*?(?<!\\)\"\"\"|b?\".*?(?<!\\)\")",
    ]


WEB_THEME = Theme(
    {
        "web.brace": Style(bold=True),
        "web.bool_true": Style(color="bright_green", italic=True),
        "web.bool_false": Style(color="bright_red", italic=True),
        "web.none": Style(color="magenta", italic=True),
        "web.path": Style(color="magenta"),
        "web.filename": Style(color="bright_magenta"),
        "web.str": Style(color="green", italic=False, bold=False),
        "web.time": Style(color="cyan"),
        "rule.text": Style(bold=True),
    }
)

logger_debug = False

# loguru auto-appends the traceback to {message} when the record carries an
# exception, so the plain file format must NOT include {exception} (it would
# print twice). The rich sinks below read `record["message"]` and build their
# own rich Traceback instead.
_PLAIN_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}"

# Styling of hr()/rule() output, resolved per render console theme:
# `rule.line` is bright_green in rich's default theme (inherited by
# WEB_THEME), `rule.text` is bold in WEB_THEME and plain on the console.
_ALAS_STYLE_KINDS = {
    "banner": "bold",
    "rule_line": "rule.line",
    "rule_title": "rule.text",
}

_stdout_console = Console()
_repr_highlighter = ReprHighlighter()
# Same grid layout RichHandler used: level column (padded, logging.level.*
# colored) + message column, 1-space padding; tracebacks render in the
# message column below the line.
_log_render = LogRender(show_time=False, show_level=True, show_path=False, level_width=None)


def _rich_renderable(record, *, time_format, highlighter, traceback_extra_lines):
    """Build the pre-loguru RichHandler-style renderable for one record.

    The rendered object carries style *names* (`logging.level.*`, `web.*`,
    `repr.*`); they resolve against whichever Console finally prints it
    (default theme on stdout, WEB_THEME in the webui parent).
    """
    level_name = record["level"].name
    level = Text.styled(f"{level_name:<8}", f"logging.level.{level_name.lower()}")

    stamp = record["time"]
    head = f"{stamp.strftime(time_format)}.{stamp.strftime('%f')[:3]} │ "
    body = Text(record["message"])

    kind = record["extra"].get("alas_style")
    if kind in _ALAS_STYLE_KINDS:
        body.stylize(_ALAS_STYLE_KINDS[kind])
        if kind == "rule_line" and record["extra"].get("alas_title") is not None:
            # Mixed rule line: chars in rule.line, the centered title in
            # rule.text (old rich Rule rendering).
            start = record["extra"]["alas_title_start"]
            body.stylize("rule.text", start, start + len(record["extra"]["alas_title"]))

    message = highlighter(Text(head) + body)

    renderables = [message]
    if record["exception"]:
        exc_type, exc_value, exc_traceback = record["exception"]
        renderables.append(
            Traceback.from_exception(
                exc_type,
                exc_value,
                exc_traceback,
                extra_lines=traceback_extra_lines,
                show_locals=True,
            )
        )

    return _log_render(_stdout_console, renderables, level=level)


def _console_sink(message):
    _stdout_console.print(
        _rich_renderable(
            message.record,
            time_format="%Y-%m-%d %H:%M:%S",
            highlighter=_repr_highlighter,
            traceback_extra_lines=3,
        )
    )


# Logger init
# Remove loguru's default stderr handler; we add our own sinks below.
_logger.remove()
# enqueue=False: the console sink must render synchronously, while the
# logging call site still holds the live traceback object. With enqueue=True
# loguru serializes the record for the worker (tracebacks are not picklable),
# the exception arrives frame-less, and rich can only print the final
# exception line — the terminal looked "concise" while the webui func sink
# (also synchronous) showed the full call chain. Same record, different
# sink timing; align them.
_console_sink_id = _logger.add(
    _console_sink,
    format="{message}",
    level="DEBUG" if logger_debug else "INFO",
    backtrace=False,
    diagnose=True,
    enqueue=False,
)

_file_sink_id = None
_func_sink_id = None
_log_file = ""

# Ensure running in Alas root folder (source runs). Installed sidecars run
# with ALAS_DATA_DIR set: gui.py already chdir'd to the writable user data
# directory, which must not be overridden here.
if not os.environ.get("ALAS_DATA_DIR"):
    os.chdir(os.path.join(os.path.dirname(__file__), "../"))

# Add file logger
pyw_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]


def _file_log_path(name=pyw_name):
    return f"./log/{datetime.date.today()}_{name}.txt"


def set_file_logger(name=pyw_name):
    global _file_sink_id, _log_file

    if _file_sink_id is not None:
        _logger.remove(_file_sink_id)
        _file_sink_id = None

    _log_file = _file_log_path(name)
    os.makedirs(os.path.dirname(_log_file), exist_ok=True)
    _file_sink_id = _logger.add(
        _log_file,
        format=_PLAIN_FORMAT,
        level="DEBUG" if logger_debug else "INFO",
        rotation="100 MB",
        compression="gz",
        encoding="utf-8",
        backtrace=False,
        diagnose=True,
        enqueue=True,
    )
    logger.log_file = _log_file


def set_func_logger(func):
    """
    Deliver rich renderables (level column + `HH:MM:SS.mmm │ ` time +
    message + rich traceback, highlighted with the legacy Highlighter and
    resolved by WEB_THEME on the parent side) into a function. Used by the
    webui child process to stream logs through a multiprocessing queue; the
    parent side keeps expecting ConsoleRenderables, unchanged.
    """
    global _func_sink_id

    if _func_sink_id is not None:
        _logger.remove(_func_sink_id)
        _func_sink_id = None

    def sink(message):
        func(
            _rich_renderable(
                message.record,
                time_format="%H:%M:%S",
                highlighter=Highlighter(),
                traceback_extra_lines=2,
            )
        )

    _func_sink_id = _logger.add(
        sink,
        format="{message}",
        level="DEBUG" if logger_debug else "INFO",
        backtrace=False,
        diagnose=True,
        enqueue=False,
    )


def rule(title="", *, characters="─", end="\n", align="center"):
    """
    Emit the ═/─ separator lines of the old rich Rule. The file sink gets
    plain text (alas.save_error_log() splits the error log on the `═`
    lines); the rich sinks restyle it via the `alas_style` extra: line
    characters in `rule.line` color and, for mixed lines, the centered
    title in `rule.text` (bold in WEB_THEME, plain on the console).
    """
    width = 60
    if title:
        text = str(title).upper()
        side = max(2, (width - len(text)) // 2)
        line = characters * side + f" {text} " + characters * max(0, width - side - len(text) - 2)
        if characters.strip():
            _logger.bind(alas_style="rule_line", alas_title=text, alas_title_start=side + 1).info(line)
        else:
            # Title-only banner line (hr level 0 center line).
            _logger.bind(alas_style="rule_title").info(line)
    else:
        line = characters * width
        _logger.bind(alas_style="rule_line").info(line)


def hr(title, level=3):
    title = str(title).upper()
    if level == 1:
        rule(title, characters="═")
        logger.info(title)
    elif level == 2:
        rule(title, characters="─")
        logger.info(title)
    elif level == 3:
        _logger.bind(alas_style="banner").info(f"<<< {title} >>>")
    elif level == 0:
        rule(characters="═")
        rule(title, characters=" ")
        rule(characters="═")


def attr(name, text):
    logger.info("[%s] %s" % (str(name), str(text)))


def attr_align(name, text, front="", align=22):
    name = str(name).rjust(align)
    if front:
        name = front + name[len(front) :]
    logger.info("%s: %s" % (name, str(text)))


def _error_convert(func):
    def error_wrapper(msg, *args, **kwargs):
        if isinstance(msg, BaseException):
            msg = f"{type(msg).__name__}: {msg}"
        return func(msg, *args, **kwargs)

    return error_wrapper


def cleanup_old_logs(directory="./log", days=30):
    """
    Delete top-level log files older than `days` (L3 retention policy).

    Only plain files directly under the directory are removed; the
    log/error/<timestamp>/ error packages (directories) are untouched.
    """
    cutoff = time.time() - days * 86400
    try:
        entries = os.listdir(directory)
    except FileNotFoundError:
        return
    for name in entries:
        path = os.path.join(directory, name)
        if not os.path.isfile(path):
            continue
        try:
            if os.path.getmtime(path) < cutoff:
                os.remove(path)
        except OSError:
            pass


def _exception_shim(e, *args, **kwargs):
    """
    logger.exception(e) legacy semantics: log the exception message at
    ERROR with its traceback (diagnose=True adds local variables).
    """
    if isinstance(e, BaseException):
        return _logger.opt(exception=e).error(str(e), *args, **kwargs)
    return _logger.opt(exception=True).error(str(e), *args, **kwargs)


# loguru ships no py.typed: declare Any so call sites keep the legacy dynamic
# surface (shims attached below) without per-site type ignores.
logger: t.Any = _logger
logger.error = _error_convert(logger.error)
logger.exception = _exception_shim
logger.hr = hr
logger.attr = attr
logger.attr_align = attr_align
logger.rule = rule
logger.set_file_logger = set_file_logger
logger.set_func_logger = set_func_logger
logger.log_file = _log_file

set_file_logger()
hr("Start", level=0)
cleanup_old_logs()
