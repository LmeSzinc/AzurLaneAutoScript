import bz2
import datetime
import gzip
import io
import logging
import multiprocessing
import os
import pathlib
import shutil
import sys
import threading
import time
from logging.handlers import TimedRotatingFileHandler
from typing import Callable, List

from rich.console import Console, ConsoleOptions, ConsoleRenderable, NewLine
from rich.highlighter import NullHighlighter, RegexHighlighter
from rich.logging import RichHandler
from rich.rule import Rule
from rich.style import Style
from rich.theme import Theme
from rich.traceback import Traceback


def empty_function(*args, **kwargs):
    pass


# cnocr will set root logger in cnocr.utils
# Delete logging.basicConfig to avoid logging the same message twice.
logging.basicConfig = empty_function
logging.raiseExceptions = True  # Set True if wanna see encode errors on console

# Remove HTTP keywords (GET, POST etc.)
RichHandler.KEYWORDS = []


class RichFileHandler(RichHandler):
    # Rename
    pass


class RichRenderableHandler(RichHandler):
    """
    Pass renderable into a function
    """

    def __init__(self, *args, func: Callable[[ConsoleRenderable], None] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._func = func

    def emit(self, record: logging.LogRecord) -> None:
        message = self.format(record)
        traceback = None
        if (
            self.rich_tracebacks
            and record.exc_info
            and record.exc_info != (None, None, None)
        ):
            exc_type, exc_value, exc_traceback = record.exc_info
            assert exc_type is not None
            assert exc_value is not None
            traceback = Traceback.from_exception(
                exc_type,
                exc_value,
                exc_traceback,
                width=self.tracebacks_width,
                extra_lines=self.tracebacks_extra_lines,
                theme=self.tracebacks_theme,
                word_wrap=self.tracebacks_word_wrap,
                show_locals=self.tracebacks_show_locals,
                locals_max_length=self.locals_max_length,
                locals_max_string=self.locals_max_string,
            )
            message = record.getMessage()
            if self.formatter:
                record.message = record.getMessage()
                formatter = self.formatter
                if hasattr(formatter, "usesTime") and formatter.usesTime():
                    record.asctime = formatter.formatTime(
                        record, formatter.datefmt)
                message = formatter.formatMessage(record)

        message_renderable = self.render_message(record, message)
        log_renderable = self.render(
            record=record, traceback=traceback, message_renderable=message_renderable
        )

        # Directly put renderable into function
        self._func(log_renderable)

    def handle(self, record: logging.LogRecord) -> bool:
        if not self._func:
            return True
        super().handle(record)


class RichTimedRotatingHandler(TimedRotatingFileHandler):
    ZIPMAP= {
        "gz" : (gzip.open, ".gz"),
        "bz2" : (bz2.open, ".bz2")
    }
    def __init__(self, zip = False, *args, **kwargs) -> None:
        TimedRotatingFileHandler.__init__(self, *args, **kwargs)
        self.console = Console(file=io.StringIO(), no_color=True, highlight=False, width=119)
        self.richd = RichHandler(
            console=self.console,
            show_path=False,
            show_time=False,
            show_level=False,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
            tracebacks_extra_lines=3,
            highlighter=NullHighlighter(),
        )
        # Keep the same format
        self.richd.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        # To handle the API of logger.print()
        self.console = self.richd.console
        # To handle the API of alas.save_error_log()
        self.log_file = None
        self.zip = zip

        # Override the initial rolloverAt
        self.rolloverAt = time.time()
        self.doRollover()
        
        # Close unnecessary stream
        self.stream.close()
        self.stream = None
        
    def getFilesToDelete(self) -> list:
        """
        Determine the files to delete when rolling over.\n
        Override the original method to use RichHandler
        """
        dirName, baseName = os.path.split(self.baseFilename)
        fileNames = os.listdir(dirName)
        result = []
        suffix = "_" + baseName
        plen = len(suffix)
        for fileName in fileNames:
            if fileName[-plen:] == suffix:
                prefix = fileName[:-plen]
                if self.extMatch.match(prefix):
                    result.append(os.path.join(dirName, fileName))
        if len(result) < self.backupCount:
            result = []
        else:
            result.sort()
            result = result[: len(result) - self.backupCount]
        return result
    
    def doRollover(self) -> None:
        """
        Do a rollover.\n
        Override the original method to use RichHandler
        """
        if self.richd.console:
            self.richd.console.file.close()
            self.richd.console.file = None

        currentTime = int(time.time())
        dstNow = time.localtime(currentTime)[-1]
        t = self.rolloverAt
        if self.utc:
            timeTuple = time.gmtime(t)
        else:
            timeTuple = time.localtime(t)
            dstThen = timeTuple[-1]
            if dstNow != dstThen:
                if dstNow:
                    addend = 3600
                else:
                    addend = -3600
                timeTuple = time.localtime(t + addend)
        
        path = pathlib.Path(self.baseFilename)
        # 2021-08-01 + _ + alas.txt -> "2021-08-01_alas.txt"
        newPath = path.with_name(
            time.strftime(self.suffix, timeTuple) + "_" + path.name
        )
        self.richd.console.file = open(
            newPath, "a" if os.path.exists(newPath) else "w", encoding="utf-8"
        )

        if self.backupCount > 0:
            for s in self.getFilesToDelete():
                os.remove(s)

        newRolloverAt = self.computeRollover(currentTime)
        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval
        # If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == "MIDNIGHT" or self.when.startswith("W")) and not self.utc:
            dstAtRollover = time.localtime(newRolloverAt)[-1]
            if dstNow != dstAtRollover:
                if (
                    not dstNow
                ):  # DST kicks in before next rollover, so we need to deduct an hour
                    addend = -3600
                else:  # DST bows out before next rollover, so we need to add an hour
                    addend = 3600
                newRolloverAt += addend
        self.rolloverAt = newRolloverAt

        if self.zip:
            thread = threading.Thread(target=self._compress, args=(self.log_file,))
            thread.daemon = True
            thread.start()
        self.log_file = str(newPath.resolve())

    def _compress(self, file, compression="bz2") -> None:
        """
        Compress a file with gzip\n
        If file is None (In the initialization), compress the last log file\n
        Template: ./log/2021-08-01_alas.txt to ./log/bak/2021-08-01_alas.txt.gz
        """
        try:
            if file is None:
                basePath = pathlib.Path(self.baseFilename)
                name = basePath.name
                logFiles = [file for file in basePath.parent.glob("*_" + name)]
                if len(logFiles) < 2:
                    return
                file = logFiles[-2]

            path = pathlib.Path(file)
            parent = path.parent
            (path.parent / "bak").mkdir(exist_ok=True)
            cmp_func, ext = self.ZIPMAP.get(compression, (gzip.open, ".gz"))
            zipFile = parent.joinpath("bak").joinpath(path.name).with_suffix(ext)

            if zipFile.exists():
                return
            with file.open("rb") as f_in:
                with cmp_func(zipFile, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
        except Exception as e:
            logger.exception(e)
    

    def print(self, *objects: ConsoleRenderable, **kwargs) -> None:
        Console.print(self.console, *objects, **kwargs)

    # @override
    def emit(self, record: logging.LogRecord) -> None:
        try:
            if self.shouldRollover(record):
                self.doRollover()
            RichHandler.emit(self.richd, record)
        except Exception:
            RichHandler.handleError(self.richd, record)


class HTMLConsole(Console):
    """
    Force full feature console
    but not working lol :(
    """
    @property
    def options(self) -> ConsoleOptions:
        return ConsoleOptions(
            max_height=self.size.height,
            size=self.size,
            legacy_windows=False,
            min_width=1,
            max_width=self.width,
            encoding='utf-8',
            is_terminal=False,
        )


class Highlighter(RegexHighlighter):
    base_style = 'web.'
    highlights = [
        # (r'(?P<datetime>(\d{2}|\d{4})(?:\-)?([0]{1}\d{1}|[1]{1}[0-2]{1})'
        #  r'(?:\-)?([0-2]{1}\d{1}|[3]{1}[0-1]{1})(?:\s)?([0-1]{1}\d{1}|'
        #  r'[2]{1}[0-3]{1})(?::)?([0-5]{1}\d{1})(?::)?([0-5]{1}\d{1}).\d+\b)'),
        (r'(?P<time>([0-1]{1}\d{1}|[2]{1}[0-3]{1})(?::)?'
         r'([0-5]{1}\d{1})(?::)?([0-5]{1}\d{1})(.\d+\b))'),
        r"(?P<brace>[\{\[\(\)\]\}])",
        r"\b(?P<bool_true>True)\b|\b(?P<bool_false>False)\b|\b(?P<none>None)\b",
        r"(?P<path>(([A-Za-z]\:)|.)?\B([\/\\][\w\.\-\_\+]+)*[\/\\])(?P<filename>[\w\.\-\_\+]*)?",
        # r"(?<![\\\w])(?P<str>b?\'\'\'.*?(?<!\\)\'\'\'|b?\'.*?(?<!\\)\'|b?\"\"\".*?(?<!\\)\"\"\"|b?\".*?(?<!\\)\")",
    ]


WEB_THEME = Theme({
    "web.brace": Style(bold=True),
    "web.bool_true": Style(color="bright_green", italic=True),
    "web.bool_false": Style(color="bright_red", italic=True),
    "web.none": Style(color="magenta", italic=True),
    "web.path": Style(color="magenta"),
    "web.filename": Style(color="bright_magenta"),
    "web.str": Style(color="green", italic=False, bold=False),
    "web.time": Style(color="cyan"),
    "rule.text": Style(bold=True),
})


# Logger init
logger_debug = False
logger = logging.getLogger('alas')
logger.setLevel(logging.DEBUG if logger_debug else logging.INFO)
file_formatter = logging.Formatter(
    fmt='%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
console_formatter = logging.Formatter(
    fmt='%(asctime)s.%(msecs)03d │ %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
web_formatter = logging.Formatter(
    fmt='%(asctime)s.%(msecs)03d │ %(message)s', datefmt='%H:%M:%S')

# Add console logger
# console = logging.StreamHandler(stream=sys.stdout)
# console.setFormatter(formatter)
# console.flush = sys.stdout.flush
# logger.addHandler(console)

# Add rich console logger
stdout_console = console = Console()
console_hdlr = RichHandler(
    show_path=False,
    show_time=False,
    rich_tracebacks=True,
    tracebacks_show_locals=True,
    tracebacks_extra_lines=3,
)
console_hdlr.setFormatter(console_formatter)
logger.addHandler(console_hdlr)

# Ensure running in Alas root folder
os.chdir(os.path.join(os.path.dirname(__file__), '../'))

# Add file logger
pyw_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]


def _set_file_logger(name=pyw_name):
    if '_' in name:
        name = name.split('_', 1)[0]
    log_file = f'./log/{datetime.date.today()}_{name}.txt'
    try:
        file = logging.FileHandler(log_file, encoding='utf-8')
    except FileNotFoundError:
        os.mkdir('./log')
        file = logging.FileHandler(log_file, encoding='utf-8')
    file.setFormatter(file_formatter)

    logger.handlers = [h for h in logger.handlers if not isinstance(
        h, (logging.FileHandler, RichFileHandler))]
    logger.addHandler(file)
    logger.log_file = log_file


def set_file_logger(name=pyw_name):
    import json
    if "_" in name:
        name = name.split("_", 1)[0]
    pname = multiprocessing.current_process().name.replace(":", "_")

    log_dir = pathlib.Path("./log")
    log_file = log_dir.joinpath(f"{pname}.txt" if name == "gui" else f"{name}.txt")
    os.makedirs(log_dir, exist_ok=True)

    # These process needn't to save log file.
    process = ["SyncManager-", "MainProcess", "Process-"]
    if any(p in log_file.name for p in process):
        hdlr = RichFileHandler(console=Console(file=io.StringIO()))
        logger.addHandler(hdlr)
        logger.log_file = str(log_file.resolve())
        if os.path.exists(log_file):
            os.remove(log_file)
        return

    valid_cfg = [
        file
        for file in pathlib.Path("./config").glob("*.json")
        if not file.name.endswith((".maa.json", ".fpy.json", "template.json"))
    ]
    if len(valid_cfg) > 0:
        try:
            with open(str(valid_cfg[0]),"r") as f:
                data_dict = json.load(f)
                cnt = data_dict.get("General", {}).get("Log", {}).get("LogBackUpCount")
                count = cnt if cnt is not None and isinstance(cnt, int) and cnt >= 0 else 7
                zip = data_dict.get("General", {}).get("Log", {}).get("EnableZip")
                zip = zip if zip is not None and isinstance(zip, bool) else False
        except Exception as e:
            count = 7
            zip = False
            logger.exception(e)
    else:
        count = 7
        zip = False
    
    hdlr = RichTimedRotatingHandler(
        zip=zip,
        filename=str(log_file),
        when="midnight",
        # when="S",
        interval=1,
        backupCount=count,
        encoding="utf-8",
    )

    logger.handlers = [
        h
        for h in logger.handlers
        if not isinstance(
            h, (logging.FileHandler, RichTimedRotatingHandler, RichFileHandler)
        )
    ]
    logger.addHandler(hdlr)
    logger.log_file = hdlr.log_file

    # Delete the default log file after initialize the handler
    if os.path.exists(log_file):
        os.remove(log_file)


def set_func_logger(func):
    console = HTMLConsole(
        force_terminal=False,
        force_interactive=False,
        width=80,
        color_system='truecolor',
        markup=False,
        safe_box=False,
        highlighter=Highlighter(),
        theme=WEB_THEME
    )
    hdlr = RichRenderableHandler(
        func=func,
        console=console,
        show_path=False,
        show_time=False,
        show_level=True,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        tracebacks_extra_lines=2,
        highlighter=Highlighter(),
    )
    hdlr.setFormatter(web_formatter)
    logger.handlers = [h for h in logger.handlers if not isinstance(
        h, RichRenderableHandler)]
    logger.addHandler(hdlr)


def _get_renderables(
    self: Console, *objects, sep=" ", end="\n", justify=None, emoji=None, markup=None, highlight=None,
) -> List[ConsoleRenderable]:
    """
    Refer to rich.console.Console.print()
    """
    if not objects:
        objects = (NewLine(),)

    render_hooks = self._render_hooks[:]
    with self:
        renderables = self._collect_renderables(
            objects,
            sep,
            end,
            justify=justify,
            emoji=emoji,
            markup=markup,
            highlight=highlight,
        )
        for hook in render_hooks:
            renderables = hook.process_renderables(renderables)
    return renderables


def print(*objects: ConsoleRenderable, **kwargs):
    for hdlr in logger.handlers:
        if isinstance(hdlr, RichRenderableHandler):
            for renderable in _get_renderables(hdlr.console, *objects, **kwargs):
                hdlr._func(renderable)
        elif isinstance(hdlr, RichHandler):
            hdlr.console.print(*objects)
        elif isinstance(hdlr, RichTimedRotatingHandler):
            hdlr.print(*objects, **kwargs)


def rule(title="", *, characters="─", style="rule.line", end="\n", align="center"):
    rule = Rule(title=title, characters=characters,
                style=style, end=end, align=align)
    print(rule)


def hr(title, level=3):
    title = str(title).upper()
    if level == 1:
        logger.rule(title, characters='═')
        logger.info(title)
    if level == 2:
        logger.rule(title, characters='─')
        logger.info(title)
    if level == 3:
        logger.info(f"[bold]<<< {title} >>>[/bold]", extra={"markup": True})
    if level == 0:
        logger.rule(characters='═')
        logger.rule(title, characters=' ')
        logger.rule(characters='═')


def attr(name, text):
    logger.info('[%s] %s' % (str(name), str(text)))


def attr_align(name, text, front='', align=22):
    name = str(name).rjust(align)
    if front:
        name = front + name[len(front):]
    logger.info('%s: %s' % (name, str(text)))


def show():
    logger.info('INFO')
    logger.warning('WARNING')
    logger.debug('DEBUG')
    logger.error('ERROR')
    logger.critical('CRITICAL')
    logger.hr('hr0', 0)
    logger.hr('hr1', 1)
    logger.hr('hr2', 2)
    logger.hr('hr3', 3)
    logger.info(r'Brace { [ ( ) ] }')
    logger.info(r'True, False, None')
    logger.info(r'E:/path\\to/alas/alas.exe, /root/alas/, ./relative/path/log.txt')
    local_var1 = 'This is local variable'
    # Line before exception
    raise Exception("Exception")
    # Line below exception


def error_convert(func):
    def error_wrapper(msg, *args, **kwargs):
        if isinstance(msg, Exception):
            msg = f'{type(msg).__name__}: {msg}'
        return func(msg, *args, **kwargs)

    return error_wrapper


logger.error = error_convert(logger.error)
logger.hr = hr
logger.attr = attr
logger.attr_align = attr_align
logger.set_file_logger = set_file_logger
logger.set_func_logger = set_func_logger
logger.rule = rule
logger.print = print
logger.log_file: str

logger.set_file_logger()
logger.hr('Start', level=0)
