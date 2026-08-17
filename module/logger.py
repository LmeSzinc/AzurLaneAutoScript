"""Logging stack backed by loguru (L1 rewrite).

The public surface is unchanged from the previous rich-logging
implementation, so the 200+ `from module.logger import logger` sites keep
working untouched:

    from module.logger import logger, set_file_logger, set_func_logger
    logger.info / warning / error / critical / debug / exception(...)
    logger.hr(title, level) / attr / attr_align / rule
    logger.log_file  (path of the active file sink)

Three sinks:

- stdout: loguru's native colorized console output (the default loguru
  handler is removed first to avoid double printing).
- file: `./log/{date}_{name}.txt` with size rotation and gz compression;
  `set_file_logger(name)` switches the active file, keeping the legacy
  date-per-name convention, and `logger.log_file` tracks it so
  alas.save_error_log() still packages the right file (the `═` separator
  lines emitted by `hr(level=0/1)` are preserved for its split regex).
- func stream: `set_func_logger(func)` delivers rich ConsoleRenderables
  (styled time/level + message + traceback, highlighted with the legacy
  Highlighter/WEB_THEME) into a callable. The webui child puts them into
  a multiprocessing queue and the parent renders them unchanged
  (process_manager.renderables / helpers.render_log), so the streaming
  contract is untouched.

Semantic notes:

- `error(Exception)` converts to "<Type>: <message>" and
  `exception(e)` logs with the traceback (diagnose=True adds local
  variables to every sink), matching the legacy handlers.
- Rich markup is no longer parsed anywhere: `hr(level=3)` writes plain
  `<<< TITLE >>>` on every sink (the old console stripped the [bold]
  tags anyway, files and webui always showed plain text).
- %-style lazy formatting is not supported (loguru uses {}); the 43
  legacy call sites were migrated in L2.
"""

import datetime
import os
import sys
import time
import typing as t

from loguru import logger as _logger
from rich.highlighter import RegexHighlighter
from rich.style import Style
from rich.text import Text
from rich.theme import Theme


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

LEVEL_STYLES = {
    "TRACE": "logging.level.trace",
    "DEBUG": "logging.level.debug",
    "INFO": "logging.level.info",
    "SUCCESS": "logging.level.success",
    "WARNING": "logging.level.warning",
    "ERROR": "logging.level.error",
    "CRITICAL": "logging.level.critical",
}

logger_debug = False

# loguru auto-appends the traceback to {message} when the record carries an
# exception, so formats must NOT include {exception} (it would print twice).
_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}"

# Logger init
# Remove loguru's default stderr handler; we add our own sinks below.
_logger.remove()
_console_sink_id = _logger.add(
    sys.stdout,
    format=_FORMAT,
    level="DEBUG" if logger_debug else "INFO",
    backtrace=False,
    diagnose=True,
    enqueue=True,
)

_file_sink_id = None
_func_sink_id = None
_log_file = ""

# Ensure running in Alas root folder
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
        format=_FORMAT,
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
    Deliver rich renderables (styled time/level + message + traceback,
    highlighted with the legacy WEB_THEME) into a function. Used by the
    webui child process to stream logs through a multiprocessing queue;
    the parent side keeps expecting ConsoleRenderables, unchanged.
    """
    global _func_sink_id

    if _func_sink_id is not None:
        _logger.remove(_func_sink_id)
        _func_sink_id = None

    def sink(message):
        record = message.record
        text = Text()
        text.append(f"{record['time'].strftime('%H:%M:%S.%f')[:-3]} │ ", style="log.time")
        level_name = record["level"].name
        text.append(f"{level_name:<8} │ ", style=LEVEL_STYLES.get(level_name, ""))
        text.append(str(message).rstrip("\n"))
        func(Highlighter()(text))

    _func_sink_id = _logger.add(
        sink,
        format="{message}",
        level="DEBUG" if logger_debug else "INFO",
        backtrace=False,
        diagnose=True,
        enqueue=False,
    )


def rule(title="", *, characters="─", style="rule.line", end="\n", align="center"):
    """
    Plain-text replacement for rich.rule.Rule. Keeps the ═/─ separator
    lines that alas.save_error_log() splits the error log on.
    """
    width = 60
    if title:
        text = str(title).upper()
        side = max(2, (width - len(text)) // 2)
        line = characters * side + f" {text} " + characters * max(0, width - side - len(text) - 2)
    else:
        line = characters * width
    logger.info(line)


def hr(title, level=3):
    title = str(title).upper()
    if level == 1:
        rule(title, characters="═")
        logger.info(title)
    elif level == 2:
        rule(title, characters="─")
        logger.info(title)
    elif level == 3:
        logger.info(f"<<< {title} >>>")
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
