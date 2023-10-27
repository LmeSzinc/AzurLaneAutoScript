"""
Copy from pywebio.pin
Add **other_html_attrs to put_xxx()
"""

from pywebio.io_ctrl import Output
from pywebio.output import OutputPosition
from pywebio.pin import _pin_output, check_dom_name_value


def put_input(name, type='text', *, label='', value=None, placeholder=None, readonly=None, datalist=None,
              help_text=None, scope=None, position=OutputPosition.BOTTOM, **other_html_attrs) -> Output:
    """Output an input widget. Refer to: `pywebio.input.input()`"""
    from pywebio.input import input
    check_dom_name_value(name, 'pin `name`')
    single_input_return = input(name=name, label=label, value=value, type=type, placeholder=placeholder,
                                readonly=readonly, datalist=datalist, help_text=help_text, **other_html_attrs)
    return _pin_output(single_input_return, scope, position)


def put_textarea(name, *, label='', rows=6, code=None, maxlength=None, minlength=None, value=None, placeholder=None,
                 readonly=None, help_text=None, scope=None, position=OutputPosition.BOTTOM, **other_html_attrs) -> Output:
    """Output a textarea widget. Refer to: `pywebio.input.textarea()`"""
    from pywebio.input import textarea
    check_dom_name_value(name, 'pin `name`')
    single_input_return = textarea(
        name=name, label=label, rows=rows, code=code, maxlength=maxlength,
        minlength=minlength, value=value, placeholder=placeholder, readonly=readonly, help_text=help_text, **other_html_attrs)
    return _pin_output(single_input_return, scope, position)


def put_select(name, options=None, *, label='', multiple=None, value=None, help_text=None,
               scope=None, position=OutputPosition.BOTTOM, **other_html_attrs) -> Output:
    """Output a select widget. Refer to: `pywebio.input.select()`"""
    from pywebio.input import select
    check_dom_name_value(name, 'pin `name`')
    single_input_return = select(name=name, options=options, label=label, multiple=multiple,
                                 value=value, help_text=help_text, **other_html_attrs)
    return _pin_output(single_input_return, scope, position)


def put_checkbox(name, options=None, *, label='', inline=None, value=None, help_text=None,
                 scope=None, position=OutputPosition.BOTTOM, **other_html_attrs) -> Output:
    """Output a checkbox widget. Refer to: `pywebio.input.checkbox()`"""
    from pywebio.input import checkbox
    check_dom_name_value(name, 'pin `name`')
    single_input_return = checkbox(name=name, options=options, label=label, inline=inline, value=value,
                                   help_text=help_text, **other_html_attrs)
    return _pin_output(single_input_return, scope, position)