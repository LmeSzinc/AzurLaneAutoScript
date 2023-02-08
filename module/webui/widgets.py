import json
import random
import string
import time
from typing import TYPE_CHECKING, Any, Callable, Dict, Generator, List, Optional, Union

from module.logger import WEB_THEME, Highlighter, HTMLConsole
from module.webui.lang import t
from module.webui.pin import put_checkbox, put_input, put_select, put_textarea
from module.webui.process_manager import ProcessManager
from module.webui.setting import State
from module.webui.utils import (
    DARK_TERMINAL_THEME,
    LIGHT_TERMINAL_THEME,
    LOG_CODE_FORMAT,
    Switch,
)
from pywebio.exceptions import SessionException
from pywebio.io_ctrl import Output
from pywebio.output import *
from pywebio.pin import pin
from pywebio.session import eval_js, local, run_js
from rich.console import ConsoleRenderable

if TYPE_CHECKING:
    from module.webui.app import AlasGUI


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
    last_display_time:dict
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
        self.display_dashboard = False
        self.first_display = True
        self.last_display_time = {'first': True}
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

    def set_dashboard_display(self, b: bool) -> None:
        # use for lambda callback function. Copied.
        self.display_dashboard = b
        self.first_display = True

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
) -> Output:
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


def put_none() -> Output:
    return put_html("<div></div>")


T_Output_Kwargs = Dict[str, Union[str, Dict[str, Any]]]


def get_title_help(kwargs: T_Output_Kwargs) -> Output:
    title: str = kwargs.get("title")
    help_text: str = kwargs.get("help")

    if help_text:
        res = put_column(
            [
                put_text(title).style("--arg-title--"),
                put_text(help_text).style("--arg-help--"),
            ],
            size="auto 1fr",
        )
    else:
        res = put_text(title).style("--arg-title--")

    return res


# args input widget
def put_arg_input(kwargs: T_Output_Kwargs) -> Output:
    name: str = kwargs["name"]
    options: List = kwargs.get("options")
    if options is not None:
        kwargs.setdefault("datalist", options)

    return put_scope(
        f"arg_container-input-{name}",
        [
            get_title_help(kwargs),
            put_input(**kwargs).style("--input--"),
        ],
    )


def put_arg_select(kwargs: T_Output_Kwargs) -> Output:
    name: str = kwargs["name"]
    value: str = kwargs["value"]
    options: List[str] = kwargs["options"]
    options_label: List[str] = kwargs.pop("options_label", [])
    disabled: bool = kwargs.pop("disabled", False)
    _: str = kwargs.pop("invalid_feedback", None)

    option = []
    if options:
        for opt, label in zip(options, options_label):
            o = {"label": label, "value": opt}
            if value == opt:
                o["selected"] = True
            else:
                o["disabled"] = disabled
            option.append(o)
    kwargs["options"] = option

    return put_scope(
        f"arg_container-select-{name}",
        [
            get_title_help(kwargs),
            put_select(**kwargs).style("--input--"),
        ],
    )


def put_arg_textarea(kwargs: T_Output_Kwargs) -> Output:
    name: str = kwargs["name"]
    mode: str = kwargs.pop("mode", None)
    kwargs.setdefault(
        "code", {"lineWrapping": True, "lineNumbers": False, "mode": mode}
    )

    return put_scope(
        f"arg_contianer-textarea-{name}",
        [
            get_title_help(kwargs),
            put_textarea(**kwargs),
        ],
    )


def put_arg_checkbox(kwargs: T_Output_Kwargs) -> Output:
    # Not real checkbox, use as a switch (on/off)
    name: str = kwargs["name"]
    value: str = kwargs["value"]
    _: str = kwargs.pop("invalid_feedback", None)

    kwargs["options"] = [{"label": "", "value": True, "selected": value}]
    return put_scope(
        f"arg_container-checkbox-{name}",
        [
            get_title_help(kwargs),
            put_checkbox(**kwargs).style("text-align: center"),
        ],
    )


def put_arg_datetime(kwargs: T_Output_Kwargs) -> Output:
    name: str = kwargs["name"]
    return put_scope(
        f"arg_container-datetime-{name}",
        [
            get_title_help(kwargs),
            put_input(**kwargs).style("--input--"),
        ],
    )


def put_arg_storage(kwargs: T_Output_Kwargs) -> Optional[Output]:
    name: str = kwargs["name"]
    if kwargs["value"] == {}:
        return None

    kwargs["value"] = json.dumps(
        kwargs["value"], indent=2, ensure_ascii=False, sort_keys=False, default=str
    )
    kwargs.setdefault(
        "code", {"lineWrapping": True, "lineNumbers": False, "mode": "json"}
    )

    def clear_callback():
        alasgui: "AlasGUI" = local.gui
        alasgui.modified_config_queue.put(
            {"name": ".".join(name.split("_")), "value": {}}
        )
        # https://github.com/pywebio/PyWebIO/issues/459
        # pin[name] = "{}"

    return put_scope(
        f"arg_container-storage-{name}",
        [
            put_textarea(**kwargs),
            put_html(
                f'<button class="btn btn-outline-warning btn-block">{t("Gui.Text.Clear")}</button>'
            ).onclick(clear_callback),
        ],
    )


_widget_type_to_func: Dict[str, Callable] = {
    "input": put_arg_input,
    "lock": put_arg_input,
    "datetime": put_arg_input,  # TODO
    "select": put_arg_select,
    "textarea": put_arg_textarea,
    "checkbox": put_arg_checkbox,
    "storage": put_arg_storage,
}


def put_output(output_kwargs: T_Output_Kwargs) -> Optional[Output]:
    return _widget_type_to_func[output_kwargs["widget_type"]](output_kwargs)


def get_loading_style(shape: str, fill: bool) -> str:
    if fill:
        return f"--loading-{shape}-fill--"
    else:
        return f"--loading-{shape}--"


def put_loading_text(
    text: str,
    shape: str = "border",
    color: str = "dark",
    fill: bool = False,
    size: str = "auto 2px 1fr",
):
    loading_style = get_loading_style(shape=shape, fill=fill)
    return put_row(
        [
            put_loading(shape=shape, color=color).style(loading_style),
            None,
            put_text(text),
        ],
        size=size,
    )
