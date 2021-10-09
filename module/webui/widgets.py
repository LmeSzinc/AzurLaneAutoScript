import random
import string

from pywebio.output import *
from pywebio.pin import *
from pywebio.session import run_js


class ScrollableCode:
    """
        https://github.com/pywebio/PyWebIO/discussions/21
    """

    def __init__(self, keep_bottom=True) -> None:
        self.keep_bottom = keep_bottom

        self.id = ''.join(random.choice(string.ascii_letters)
                          for _ in range(10))
        self.html = '<pre id="%s"><code style="white-space:break-spaces;"></code></pre>' % self.id
        self.output = put_html(self.html)

    def append(self, text):
        if text:
            run_js("""$("#{dom_id}>code").append(text);
            """.format(dom_id=self.id), text=str(text))
            if self.keep_bottom:
                self.scroll()

    def scroll(self):
        run_js(r"""$("\#{dom_id}").animate({{scrollTop: $("\#{dom_id}").prop("scrollHeight")}}, 0);
        """.format(dom_id=self.id))

    def reset(self):
        self.output.reset(put_html(self.html))

    def set_scroll(self, b):
        # use for lambda callback function
        self.keep_bottom = b


# aside buttons
def put_icon_buttons(icon_html, *args, **kwargs):
    return output(put_column([
        output(put_html(icon_html)).style(
            "z-index: 1; margin-left: 8px;text-align: center"),
        put_buttons(*args, **kwargs).style("z-index: 2;")
    ], size="0"))

# args input widget


def put_input_(name, title, help=None, value='', width="12rem", readonly=None):
    return output(
        put_row([
            put_column([
                put_text(title).style("arg-title"),
                put_text(help).style("arg-help"),
            ], size="auto auto"),
            put_input(name, value=value, readonly=readonly).style("input-input")
        ], size=f"1fr {width}")
    ).style("container-args") if help \
        else output(
        put_row([
            put_text(title).style("arg-title"),
            put_input(name, value=value, readonly=readonly).style("input-input")
        ], size=f"1fr {width}")
    ).style("container-args")


def put_select_(name, title, help=None, options=[], width="12rem"):
    return output(
        put_row([
            put_column([
                put_text(title).style("arg-title"),
                put_text(help).style("arg-help"),
            ], size="auto auto"),
            put_select(name, options=options).style("input-input")
        ], size=f"1fr {width}")
    ).style("container-args") if help \
        else output(
        put_row([
            put_text(title).style("arg-title"),
            put_select(name, options=options).style("input-input")
        ], size=f"1fr {width}")
    ).style("container-args")


def put_textarea_(name, title, help=None, value='', readonly=None):
    return output(
        put_column([
            put_text(title).style("arg-title"),
            put_text(help).style("arg-help"),
            put_textarea(name, value=value, readonly=readonly, code={
                         "theme": "idea", "lineWrapping": True, "lineNumbers": False})
        ], size="auto auto auto")
    ).style("container-args") if help \
        else output(
        put_column([
            put_text(title).style("arg-title"),
            put_textarea(name, value=value, readonly=readonly, code={
                         "theme": "idea", "lineWrapping": True, "lineNumbers": False})
        ], size="auto auto")
    ).style("container-args")


def put_checkbox_(name, title, help=None, value=False, width="12rem"):
    # Not real checkbox, use as a switch (on/off)
    return output(
        put_row([
            put_column([
                put_text(title).style("arg-title"),
                put_text(help).style("arg-help"),
            ], size="auto auto"),
            put_checkbox(name, options=[{'label': '', 'value': True, 'selected': value}]).style(
                "text-align: center")
        ], size=f"1fr {width}")
    ).style("container-large.args") if help \
        else output(
        put_row([
            put_text(title).style("arg-title"),
            put_checkbox(name, options=[{'label': '', 'value': True, 'selected': value}]).style(
                "text-align: center")
        ], size=f"1fr {width}")
    ).style("container-large.args")


# arg block
def put_group(title, help=None):
    return output(
        put_text(title).style("group-title"),
        put_text(help).style("group-help"),
        put_html('<hr class="hr-group">'),
    ).style("container-group") if help \
        else output(
        put_text(title).style("group-title"),
        put_html('<hr class="hr-group">'),
    ).style("container-group")
