import random
import string
from typing import Callable, Dict, Generator, List, Union

from pywebio.exceptions import SessionException
from pywebio.output import *
from pywebio.session import eval_js, run_js
from rich.console import ConsoleRenderable

from module.logger import WEB_THEME, Highlighter, HTMLConsole
from module.webui.pin import put_checkbox, put_input, put_select, put_textarea
from module.webui.process_manager import ProcessManager
from module.webui.setting import State
from module.webui.utils import (DARK_TERMINAL_THEME, LIGHT_TERMINAL_THEME,
                                LOG_CODE_FORMAT, Switch)


class ScrollableCode:
    """
    https://github.com/pywebio/PyWebIO/discussions/21
    Deprecated
    """

    def __init__(self, keep_bottom: bool = True) -> None:
        self.keep_bottom = keep_bottom

        self.id = "".join(random.choice(string.ascii_letters) for _ in range(10))
        self.html = (
            """<pre id="%s" class="container-log"><code style="white-space:break-spaces;"></code></pre>"""
            % self.id
        )

    def output(self):
        # .style("display: grid; overflow-y: auto;")
        return put_html(self.html)

    def append(self, text: str) -> None:
        if text:
            run_js(
                """$("#{dom_id}>code").append(text);
            """.format(
                    dom_id=self.id
                ),
                text=str(text),
            )
            if self.keep_bottom:
                self.scroll()

    def scroll(self) -> None:
        run_js(
            r"""$("\#{dom_id}").animate({{scrollTop: $("\#{dom_id}").prop("scrollHeight")}}, 0);
        """.format(
                dom_id=self.id
            )
        )

    def reset(self) -> None:
        run_js(r"""$("\#{dom_id}>code").empty();""".format(dom_id=self.id))

    def set_scroll(self, b: bool) -> None:
        # use for lambda callback function
        self.keep_bottom = b


class RichLog:
    def __init__(self, scope, font_width="0.559") -> None:
        self.scope = scope
        self.font_width = font_width
        self.console = HTMLConsole(
            force_terminal=False,
            force_interactive=False,
            width=80,
            color_system="truecolor",
            markup=False,
            record=True,
            safe_box=False,
            highlighter=Highlighter(),
            theme=WEB_THEME,
        )
        # self.callback_id = output_register_callback(
        #     self._callback_set_width, serial_mode=True)
        # self._callback_thread = None
        # self._width = 80
        self.keep_bottom = True
        if State.theme == "dark":
            self.terminal_theme = DARK_TERMINAL_THEME
        else:
            self.terminal_theme = LIGHT_TERMINAL_THEME

    def render(self, renderable: ConsoleRenderable) -> str:
        with self.console.capture():
            self.console.print(renderable)

        html = self.console.export_html(
            theme=self.terminal_theme,
            clear=True,
            code_format=LOG_CODE_FORMAT,
            inline_styles=True,
        )
        # print(html)
        return html

    def extend(self, text):
        if text:
            run_js(
                """$("#pywebio-scope-{scope}>div").append(text);
            """.format(
                    scope=self.scope
                ),
                text=str(text),
            )
            if self.keep_bottom:
                self.scroll()

    def reset(self):
        run_js(f"""$("#pywebio-scope-{self.scope}>div").empty();""")

    def scroll(self) -> None:
        run_js(
            """$("#pywebio-scope-{scope}").scrollTop($("#pywebio-scope-{scope}").prop("scrollHeight"));
        """.format(
                scope=self.scope
            )
        )

    def set_scroll(self, b: bool) -> None:
        # use for lambda callback function
        self.keep_bottom = b

    def get_width(self):
        js = """
        let canvas = document.createElement('canvas');
        canvas.style.position = "absolute";
        let ctx = canvas.getContext('2d');
        document.body.appendChild(canvas);
        ctx.font = `16px Menlo, consolas, DejaVu Sans Mono, Courier New, monospace`;
        document.body.removeChild(canvas);
        let text = ctx.measureText('0');
        ctx.fillText('0', 50, 50);

        ($('#pywebio-scope-{scope}').width()-16)/\
        $('#pywebio-scope-{scope}').css('font-size').slice(0, -2)/text.width*16;\
        """.format(
            scope=self.scope
        )
        width = eval_js(js)
        return 80 if width is None else 128 if width > 128 else int(width)

    # def _register_resize_callback(self):
    #     js = """
    #     WebIO.pushData(
    #         ($('#pywebio-scope-log').width()-16)/$('#pywebio-scope-log').css('font-size').slice(0, -2)/0.55,
    #         {callback_id}
    #     )""".format(callback_id=self.callback_id)

    # def _callback_set_width(self, width):
    #     self._width = width
    #     if self._callback_thread is None:
    #         self._callback_thread = Thread(target=self._callback_width_checker)
    #         self._callback_thread.start()

    # def _callback_width_checker(self):
    #     last_modify = time.time()
    #     _width = self._width
    #     while True:
    #         if time.time() - last_modify > 1:
    #             break
    #         if self._width == _width:
    #             time.sleep(0.1)
    #             continue
    #         else:
    #             _width = self._width
    #             last_modify = time.time()

    #     self._callback_thread = None
    #     self.console.width = int(_width)

    def put_log(self, pm: ProcessManager) -> Generator:
        yield
        try:
            while True:
                last_idx = len(pm.renderables)
                html = "".join(map(self.render, pm.renderables[:]))
                self.reset()
                self.extend(html)
                counter = last_idx
                while counter < pm.renderables_max_length * 2:
                    yield
                    idx = len(pm.renderables)
                    if idx < last_idx:
                        last_idx -= pm.renderables_reduce_length
                    if idx != last_idx:
                        html = "".join(map(self.render, pm.renderables[last_idx:idx]))
                        self.extend(html)
                        counter += idx - last_idx
                        last_idx = idx
        except SessionException:
            pass


class BinarySwitchButton(Switch):
    def __init__(
        self,
        get_state,
        label_on,
        label_off,
        onclick_on,
        onclick_off,
        scope,
        color_on="success",
        color_off="secondary",
    ):
        """
        Args:
            get_state:
                (Callable):
                    return True to represent state `ON`
                    return False tp represent state `OFF`
                (Generator):
                    yield True to change btn state to `ON`
                    yield False to change btn state to `OFF`
            label_on: label to show when state is `ON`
            label_off:
            onclick_on: function to call when state is `ON`
            onclick_off:
            color_on: button color when state is `ON`
            color_off:
            scope: scope for button, just for button **only**
        """
        self.scope = scope
        status = {
            0: {
                "func": self.update_button,
                "args": (
                    label_off,
                    onclick_off,
                    color_off,
                ),
            },
            1: {
                "func": self.update_button,
                "args": (
                    label_on,
                    onclick_on,
                    color_on,
                ),
            },
        }
        super().__init__(status=status, get_state=get_state, name=scope)

    def update_button(self, label, onclick, color):
        clear(self.scope)
        put_button(label=label, onclick=onclick, color=color, scope=self.scope)


# aside buttons


def put_icon_buttons(
    icon_html: str,
    buttons: List[Dict[str, str]],
    onclick: Union[List[Callable[[], None]], Callable[[], None]],
):
    value = buttons[0]["value"]
    return put_column(
        [
            output(put_html(icon_html)).style(
                "z-index: 1; margin-left: 8px;text-align: center"
            ),
            put_buttons(buttons, onclick).style(f"z-index: 2; --aside-{value}--;"),
        ],
        size="0",
    )


# args input widget
def put_input_(
    name: str,
    title: str,
    help: str = None,
    value: str = "",
    readonly: bool = None,
    **other_html_attrs,
):
    if help:
        left = put_column(
            [
                put_text(title).style("--arg-title--"),
                put_text(help).style("--arg-help--"),
            ],
            size="auto 1fr",
        )
    else:
        left = put_text(title).style("--arg-title--")

    return put_row(
        [
            left,
            put_input(name, value=value, readonly=readonly, **other_html_attrs).style(
                "--input--"
            ),
        ]
    ).style("container-args-row")


def put_select_(
    name: str,
    title: str,
    help: str = None,
    options: List[str] = None,
    **other_html_attrs,
):
    if options is None:
        options = []
    if help:
        left = put_column(
            [
                put_text(title).style("--arg-title--"),
                put_text(help).style("--arg-help--"),
            ],
            size="auto 1fr",
        )
    else:
        left = put_text(title).style("--arg-title--")

    return put_row(
        [
            left,
            put_select(name, options=options, **other_html_attrs).style("--input--"),
        ]
    ).style("container-args-row")


def put_textarea_(
    name: str,
    title: str,
    help: str = None,
    value: str = "",
    readonly: bool = None,
    **other_html_attrs,
):
    if help:
        return put_column(
            [
                put_text(title).style("--arg-title--"),
                put_text(help).style("--arg-help--"),
                put_textarea(
                    name,
                    value=value,
                    readonly=readonly,
                    code={"lineWrapping": True, "lineNumbers": False},
                    **other_html_attrs,
                ),
            ],
            size="auto auto auto",
        ).style("container-args-column")
    else:
        return put_column(
            [
                put_text(title).style("--arg-title--"),
                put_textarea(
                    name,
                    value=value,
                    readonly=readonly,
                    code={"lineWrapping": True, "lineNumbers": False},
                    **other_html_attrs,
                ),
            ],
            size="auto auto",
        ).style("container-args-column")


def put_checkbox_(
    name: str, title: str, help: str = None, value: bool = False, **other_html_attrs
):
    # Not real checkbox, use as a switch (on/off)
    if help:
        left = put_column(
            [
                put_text(title).style("--arg-title--"),
                put_text(help).style("--arg-help--"),
            ],
            size="auto 1fr",
        )
    else:
        left = put_text(title).style("--arg-title--")

    return put_row(
        [
            left,
            put_checkbox(
                name,
                options=[{"label": "", "value": True, "selected": value}],
                **other_html_attrs,
            ).style("text-align: center"),
        ]
    ).style("container-large.args")


def put_none():
    return put_html("<div></div>")


def get_output(
    arg_type, name, title, arg_help=None, value=None, options=None, **other_html_attrs
):
    if arg_type == "input":
        return put_input_(name, title, arg_help, value, **other_html_attrs)
    elif arg_type == "select":
        return put_select_(name, title, arg_help, options, **other_html_attrs)
    elif arg_type == "textarea":
        return put_textarea_(name, title, arg_help, value, **other_html_attrs)
    elif arg_type == "checkbox":
        return put_checkbox_(name, title, arg_help, value, **other_html_attrs)
    elif arg_type == "lock":
        return put_input_(
            name, title, arg_help, value, readonly=True, **other_html_attrs
        )
    elif arg_type == "disable":
        return put_input_(
            name, title, arg_help, value, readonly=True, **other_html_attrs
        )
    elif arg_type == "hide":
        return None
