import random
import string
from typing import Callable, Dict, List, Union

from pywebio.output import *
from pywebio.pin import *
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
        self.output = output(put_html(self.html)).style("display: grid; overflow-y: auto;")

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
    width: str = "12rem", 
    readonly: bool = None
):
    if help:
        left = put_column([
            put_text(title).style("arg-title"),
            put_text(help).style("arg-help"),
        ], size="auto auto")
    else:
        left = put_text(title).style("arg-title")
    
    return put_row([
        left,
        put_input(name, value=value, readonly=readonly).style("input-input"),
    ], size=f"1fr {width}").style("container-args")


def put_select_(
    name: str, 
    title: str, 
    help: str = None,
    options: List[str] = None,
    width: str = "12rem"
):
    if options is None:
        options = []
    if help:
        left = put_column([
            put_text(title).style("arg-title"),
            put_text(help).style("arg-help"),
        ], size="auto auto")
    else:
        left = put_text(title).style("arg-title")
    
    return put_row([
        left,
        put_select(name, options=options).style("input-input"),
    ], size=f"1fr {width}").style("container-args")


def put_textarea_(
    name: str, 
    title: str, 
    help: str = None, 
    value: str = '', 
    readonly: bool = None
):
    if help:
        return put_column([
            put_text(title).style("arg-title"),
            put_text(help).style("arg-help"),
            put_textarea(name, value=value, readonly=readonly, code={
                "theme": "idea", "lineWrapping": True, "lineNumbers": False})
        ], size="auto auto auto").style("container-args")
    else:
        return put_column([
            put_text(title).style("arg-title"),
            put_textarea(name, value=value, readonly=readonly, code={
                "theme": "idea", "lineWrapping": True, "lineNumbers": False})
        ], size="auto auto").style("container-args")


def put_checkbox_(
    name: str,
    title: str, 
    help: str = None, 
    value: bool = False, 
    width: str = "12rem", 
):
    # Not real checkbox, use as a switch (on/off)
    if help:
        left = put_column([
            put_text(title).style("arg-title"),
            put_text(help).style("arg-help"),
        ], size="auto auto")
    else:
        left = put_text(title).style("arg-title")
    
    return put_row([
        left,
        put_checkbox(
            name,
            options=[{'label': '', 'value': True, 'selected': value}]
        ).style("text-align: center")
    ], size=f"1fr {width}").style("container-large.args")


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
