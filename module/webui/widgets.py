import random
import string
from typing import Callable, Dict, List, Union

from module.webui.pin import put_checkbox, put_input, put_select, put_textarea
from pywebio.output import *
from pywebio.session import run_js


class ScrollableCode:
    """
        https://github.com/pywebio/PyWebIO/discussions/21
    """

    def __init__(self, keep_bottom: bool = True) -> None:
        self.keep_bottom = keep_bottom

        self.id = ''.join(random.choice(string.ascii_letters)
                          for _ in range(10))
        self.html = """<pre id="%s" class="container-log"><code style="white-space:break-spaces;"></code></pre>"""\
            % self.id
        self.output = output(put_html(self.html)).style(
            "display: grid; overflow-y: auto;")

    def append(self, text: str) -> None:
        if text:
            run_js("""$("#{dom_id}>code").append(text);
            """.format(dom_id=self.id), text=str(text))
            if self.keep_bottom:
                self.scroll()

    def scroll(self) -> None:
        run_js(r"""$("\#{dom_id}").animate({{scrollTop: $("\#{dom_id}").prop("scrollHeight")}}, 0);
        """.format(dom_id=self.id))

    def reset(self) -> None:
        self.output.reset(put_html(self.html))

    def set_scroll(self, b: bool) -> None:
        # use for lambda callback function
        self.keep_bottom = b


# aside buttons
def put_icon_buttons(icon_html: str,
                     buttons: List[Dict[str, str]],
                     onclick: Union[List[Callable[[], None]], Callable[[], None]]):
    value = buttons[0]['value']
    return put_column([
        output(put_html(icon_html)).style(
            "z-index: 1; margin-left: 8px;text-align: center"),
        put_buttons(buttons, onclick).style(f"z-index: 2; --aside-{value}--;")
    ], size="0")


# args input widget
def put_input_(
    name: str,
    title: str,
    help: str = None,
    value: str = '',
    readonly: bool = None,
    **other_html_attrs
):
    if help:
        left = put_column([
            put_text(title).style("arg-title"),
            put_text(help).style("arg-help"),
        ], size="auto 1fr")
    else:
        left = put_text(title).style("arg-title")

    return put_row([
        left,
        put_input(name, value=value, readonly=readonly, **
                  other_html_attrs).style("input-input"),
    ]).style("container-args-row")


def put_select_(
    name: str,
    title: str,
    help: str = None,
    options: List[str] = None,
    **other_html_attrs
):
    if options is None:
        options = []
    if help:
        left = put_column([
            put_text(title).style("arg-title"),
            put_text(help).style("arg-help"),
        ], size="auto 1fr")
    else:
        left = put_text(title).style("arg-title")

    return put_row([
        left,
        put_select(name, options=options, **
                   other_html_attrs).style("input-input"),
    ]).style("container-args-row")


def put_textarea_(
    name: str,
    title: str,
    help: str = None,
    value: str = '',
    readonly: bool = None,
    **other_html_attrs
):
    if help:
        return put_column([
            put_text(title).style("arg-title"),
            put_text(help).style("arg-help"),
            put_textarea(name, value=value, readonly=readonly, code={
                "lineWrapping": True, "lineNumbers": False}, **other_html_attrs)
        ], size="auto auto auto").style("container-args-column")
    else:
        return put_column([
            put_text(title).style("arg-title"),
            put_textarea(name, value=value, readonly=readonly, code={
                "lineWrapping": True, "lineNumbers": False}, **other_html_attrs)
        ], size="auto auto").style("container-args-column")


def put_checkbox_(
    name: str,
    title: str,
    help: str = None,
    value: bool = False,
    **other_html_attrs
):
    # Not real checkbox, use as a switch (on/off)
    if help:
        left = put_column([
            put_text(title).style("arg-title"),
            put_text(help).style("arg-help"),
        ], size="auto 1fr")
    else:
        left = put_text(title).style("arg-title")

    return put_row([
        left,
        put_checkbox(
            name,
            options=[{'label': '', 'value': True, 'selected': value}],
            **other_html_attrs
        ).style("text-align: center")
    ]).style("container-large.args")


# arg block
def put_group(title, help: str = None):
    return output(
        put_text(title).style("group-title"),
        put_text(help).style("group-help"),
        put_html('<hr class="hr-group">'),
    ).style("container-group") if help \
        else output(
        put_text(title).style("group-title"),
        put_html('<hr class="hr-group">'),
    ).style("container-group")
