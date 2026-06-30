# This module is a ton of shit
# you'd better close right now
from pywebio.input import (actions, checkbox, input, input_group, input_update,
                           select)
from pywebio.output import put_buttons, put_markdown
from pywebio.session import defer_call, hold, run_js, set_env

import module.webui.lang as lang
from module.config.deep import deep_get, deep_iter, deep_set
from module.config.utils import LANGUAGES, filepath_i18n, read_file, write_file


def translate():
    """
        Translate Alas
    """
    set_env(output_animation=False)
    run_js(r"""$('head').append('<style>footer {display: none}</style>')""")

    put_markdown("""
        # Translate
        You can submit(Next) by press `Enter`.
    """)

    dict_lang = {
        "zh-CN": read_file(filepath_i18n('zh-CN')),
        "zh-TW": read_file(filepath_i18n('zh-TW')),
        "en-US": read_file(filepath_i18n('en-US')),
        "ja-JP": read_file(filepath_i18n('ja-JP')),
    }
    modified = {
        "zh-CN": {},
        "zh-TW": {},
        "en-US": {},
        "ja-JP": {},
    }

    list_path = []  # Menu.Task.name
    list_group = []  # Menu
    list_arg = []  # Task
    list_key = []  # name
    for L, _ in deep_iter(dict_lang['zh-CN'], depth=3):
        list_path.append('.'.join(L))
        list_group.append(L[0])
        list_arg.append(L[1])
        list_key.append(L[2])
    total = len(list_path)

    class V:
        lang = lang.LANG
        untranslated_only = False
        clear = False

        idx = -1
        group = ''
        group_idx = 0
        groups = list(dict_lang['zh-CN'].keys())
        arg = ''
        arg_idx = 0
        args = []
        key = ''
        key_idx = 0
        keys = []

    def update_var(group=None, arg=None, key=None):
        if group:
            V.group = group
            V.idx = list_group.index(group)
            V.group_idx = V.idx
            V.arg = list_arg[V.idx]
            V.arg_idx = V.idx
            V.args = list(dict_lang["zh-CN"][V.group].keys())
            V.key = list_key[V.idx]
            V.key_idx = V.idx
            V.keys = list(dict_lang["zh-CN"][V.group][V.arg].keys())
        elif arg:
            V.arg = arg
            V.idx = list_arg.index(arg, V.group_idx)
            V.arg_idx = V.idx
            V.args = list(dict_lang["zh-CN"][V.group].keys())
            V.key = list_key[V.idx]
            V.key_idx = V.idx
            V.keys = list(dict_lang["zh-CN"][V.group][V.arg].keys())
        elif key:
            V.key = key
            V.idx = list_key.index(key, V.arg_idx)
            V.key_idx = V.idx
            V.keys = list(dict_lang["zh-CN"][V.group][V.arg].keys())

        update_form()

    def next_key():
        if V.idx + 1 > total:
            V.idx = -1

        V.idx += 1

        if V.untranslated_only:
            while True:
                # print(V.idx)
                key = deep_get(dict_lang[V.lang], list_path[V.idx])
                if list_path[V.idx] == key or list_path[V.idx].split('.')[2] == key:
                    break
                else:
                    V.idx += 1
                if V.idx + 1 > total:
                    V.idx = 0
                    break

        (V.group, V.arg, V.key) = tuple(list_path[V.idx].split('.'))
        V.group_idx = list_group.index(V.group)
        V.arg_idx = list_arg.index(V.arg, V.group_idx)
        V.args = list(dict_lang["zh-CN"][V.group].keys())
        V.key_idx = list_key.index(V.key, V.arg_idx)
        V.keys = list(dict_lang["zh-CN"][V.group][V.arg].keys())

    def update_form():
        input_update('arg', options=V.args, value=V.arg)
        input_update('key', options=V.keys, value=V.key)
        for L in LANGUAGES:
            input_update(L, value=deep_get(
                dict_lang[L], f'{V.group}.{V.arg}.{V.key}', 'Key not found!'))

        old = deep_get(dict_lang[V.lang],
                       f'{V.group}.{V.arg}.{V.key}', 'Key not found!')
        input_update(V.lang,
                     value=None if V.clear else old,
                     help_text=f'{V.group}.{V.arg}.{V.key}',
                     placeholder=old,
                     )

    def get_inputs():
        out = []
        old = deep_get(dict_lang[V.lang],
                       f'{V.group}.{V.arg}.{V.key}', 'Key not found!')
        out.append(
            input(
                name=V.lang,
                label=V.lang,
                value=None if V.clear else old,
                help_text=f'{V.group}.{V.arg}.{V.key}',
                placeholder=old,
            )
        )
        out.append(
            select(name='group', label='Group', options=V.groups, value=V.group,
                   onchange=lambda g: update_var(group=g), required=True)
        )
        out.append(
            select(name='arg', label='Arg', options=V.args, value=V.arg,
                   onchange=lambda a: update_var(arg=a), required=True)
        )
        out.append(
            select(name='key', label='Key', options=V.keys, value=V.key,
                   onchange=lambda k: update_var(key=k), required=True)
        )
        _LANGUAGES = LANGUAGES.copy()
        _LANGUAGES.remove(V.lang)
        for L in _LANGUAGES:
            out.append(
                input(name=L, label=L, readonly=True, value=deep_get(
                    dict_lang[L], f'{V.group}.{V.arg}.{V.key}', 'Key not found!'))
            )
        out.append(
            actions(name='action', buttons=[
                {"label": "Next", "value": 'Next',
                    "type": "submit", "color": "success"},
                {"label": "Next without save", "value": 'Skip',
                    "type": "submit", "color": "secondary"},
                {"label": "Submit", "value": "Submit",
                    "type": "submit", "color": "primary"},
                {"label": "Quit and save", "type": "cancel", "color": "secondary"},
            ])
        )

        return out

    def save():
        for LANG in LANGUAGES:
            d = read_file(filepath_i18n(LANG))
            for k in modified[LANG].keys():
                deep_set(d, k, modified[LANG][k])
            write_file(filepath_i18n(LANG), d)
    defer_call(save)

    def loop():
        while True:
            data = input_group(inputs=get_inputs())
            if data is None:
                save()
                break

            if data['action'] == 'Next':

                modified[V.lang][f'{V.group}.{V.arg}.{V.key}'] = data[V.lang].replace(
                    "\\n", "\n")
                deep_set(dict_lang[V.lang], f'{V.group}.{V.arg}.{V.key}', data[V.lang].replace(
                    "\\n", "\n"))
                next_key()
            if data['action'] == 'Skip':
                next_key()
            elif data['action'] == 'Submit':

                modified[V.lang][f'{V.group}.{V.arg}.{V.key}'] = data[V.lang].replace(
                    "\\n", "\n")
                deep_set(dict_lang[V.lang], f'{V.group}.{V.arg}.{V.key}', data[V.lang].replace(
                    "\\n", "\n"))
                continue

    def setting():
        data = input_group(inputs=[
            select(name='language', label='Language',
                   options=LANGUAGES, value=V.lang, required=True),
            checkbox(name='check', label='Other settings', options=[
                {"label": 'Button [Next] only shows untranslated key',
                    'value': 'untranslated', 'selected': V.untranslated_only},
                {"label": 'Do not fill input with old value (only effect the language you selected)',
                 "value": "clear", "selected": V.clear}
            ])
        ])
        V.lang = data['language']
        V.untranslated_only = True if 'untranslated' in data['check'] else False
        V.clear = True if 'clear' in data['check'] else False

    put_buttons([
        {"label": "Start", "value": "start"},
        {"label": "Setting", "value": "setting"}
    ], onclick=[loop, setting])
    next_key()
    setting()
    hold()
