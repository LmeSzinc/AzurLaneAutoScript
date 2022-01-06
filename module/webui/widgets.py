import random
import string
from typing import Callable, Dict, Generator, List, Union

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

    def output(self):
        # .style("display: grid; overflow-y: auto;")
        return put_html(self.html)

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
        run_js(r"""$("\#{dom_id}>code").empty();""".format(dom_id=self.id))

    def set_scroll(self, b: bool) -> None:
        # use for lambda callback function
        self.keep_bottom = b


class Switch:
    def __init__(
        self,
        label_on='ON',
        label_off='Turn on',
        onclick_on=lambda: toast('You just turn it off'),
        onclick_off=lambda: toast('Its on now'),
        get_status=lambda: 1,
        color_on='success',
        color_off='secondary',
        scope='scope_btn'
    ):
        """
        Args:
            get_status: 
                (Callable): 
                    return True to represent state `ON`
                    False represent state `OFF`
                (Generator):
                    yield 1 to represent change btn state to `ON`
                    yield -1 to represent change btn state to `OFF`
                    yield 0 do nothing
            label_on: label to show when state is `ON`
            label_off: 
            onclick_on: function to call when state is `ON`
            onclick_off:
            color_on: button color when state is `ON`
            color_off:
            scope: scope for button, just for button **only**

            *Summary: *_on belongs to state `ON`
        """
        self.label_on = label_on
        self.label_off = label_off
        self.on = onclick_on
        self.off = onclick_off
        self.color_on = color_on
        self.color_off = color_off
        self.scope = scope
        if isinstance(get_status, Generator):
            self.get_status = get_status
        elif isinstance(get_status, Callable):
            self.get_status = self._get_status(get_status)

    def on(self):
        pass

    def off(self):
        pass

    def _get_status(self, func: Callable):
        status = func()
        yield 1 if status else -1
        while True:
            if status != func():
                status = func()
                yield 1 if status else -1
                continue
            yield 0

    def refresh(self):
        r = next(self.get_status)
        if r == 1:
            clear(self.scope)
            put_button(
                label=self.label_on,
                onclick=self.on,
                color=self.color_on,
                scope=self.scope
            )
        elif r == -1:
            clear(self.scope)
            put_button(
                label=self.label_off,
                onclick=self.off,
                color=self.color_off,
                scope=self.scope
            )

    def g(self):
        def _g():
            while True:
                yield self.refresh()
        g = _g()
        g.__name__ = f"refresh_{self.scope}"
        return g


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
            put_text(title).style("--arg-title--"),
            put_text(help).style("--arg-help--"),
        ], size="auto 1fr")
    else:
        left = put_text(title).style("--arg-title--")

    return put_row([
        left,
        put_input(name, value=value, readonly=readonly, **
                  other_html_attrs).style("--input--"),
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
            put_text(title).style("--arg-title--"),
            put_text(help).style("--arg-help--"),
        ], size="auto 1fr")
    else:
        left = put_text(title).style("--arg-title--")

    return put_row([
        left,
        put_select(name, options=options, **
                   other_html_attrs).style("--input--"),
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
            put_text(title).style("--arg-title--"),
            put_text(help).style("--arg-help--"),
            put_textarea(name, value=value, readonly=readonly, code={
                "lineWrapping": True, "lineNumbers": False}, **other_html_attrs)
        ], size="auto auto auto").style("container-args-column")
    else:
        return put_column([
            put_text(title).style("--arg-title--"),
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
            put_text(title).style("--arg-title--"),
            put_text(help).style("--arg-help--"),
        ], size="auto 1fr")
    else:
        left = put_text(title).style("--arg-title--")

    return put_row([
        left,
        put_checkbox(
            name,
            options=[{'label': '', 'value': True, 'selected': value}],
            **other_html_attrs
        ).style("text-align: center")
    ]).style("container-large.args")


def put_none():
    return put_html('<div></div>')
